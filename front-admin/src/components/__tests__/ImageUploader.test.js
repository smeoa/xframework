import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { mount } from "@vue/test-utils";
import ImageUploader from "../ImageUploader.vue";

// ── Mocks ────────────────────────────────────────────────────

const { mockElMessage, mockElMessageWarning, mockElMessageSuccess, mockElMessageError } = vi.hoisted(() => ({
  mockElMessage: vi.fn(),
  mockElMessageWarning: vi.fn(),
  mockElMessageSuccess: vi.fn(),
  mockElMessageError: vi.fn(),
}));

vi.mock("@/utils/request", () => ({
  default: {
    post: vi.fn(),
  },
}));

vi.mock("element-plus", () => ({
  ElMessage: Object.assign(mockElMessage, {
    warning: mockElMessageWarning,
    success: mockElMessageSuccess,
    error: mockElMessageError,
    info: vi.fn(),
  }),
}));

// Stub all Element Plus components the uploader uses
const globalStubs = {
  "el-icon": { template: "<i class='el-icon-stub'><slot /></i>" },
  "el-button": { template: "<button class='el-button-stub'><slot /></button>" },
  "el-progress": {
    template:
      '<div class="el-progress-stub">{{ percentage }}%</div>',
    props: ["percentage", "width", "stroke-width", "color"],
  },
  "el-image-viewer": {
    template:
      '<div class="el-image-viewer-stub" @click="$emit(\'close\')">Preview</div>',
    props: ["url-list", "initial-index", "hide-on-click-modal"],
    emits: ["close"],
  },
  "el-input-number": {
    template: '<input class="el-input-number-stub" />',
  },
};

// ── Helpers ──────────────────────────────────────────────────

function createFile(name, type = "image/png", size = 1024) {
  const blob = new Blob([new ArrayBuffer(size)], { type });
  return new File([blob], name, { type });
}

// ── Tests ────────────────────────────────────────────────────

describe("ImageUploader.vue", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Stub URL.createObjectURL / revokeObjectURL
    vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:mock-url");
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ── Rendering ──────────────────────────────────────────────

  describe("rendering", () => {
    it("renders the upload zone with text", () => {
      const wrapper = mount(ImageUploader, { global: { stubs: globalStubs } });
      expect(wrapper.find(".upload-zone").exists()).toBe(true);
      expect(wrapper.text()).toContain("粘贴图片");
    });

    it("renders existing images from modelValue", () => {
      const modelValue = [
        { uid: 1, url: "https://example.com/img1.png", title: "Image 1" },
        { uid: 2, url: "https://example.com/img2.png", title: "Image 2" },
      ];
      const wrapper = mount(ImageUploader, {
        props: { modelValue },
        global: { stubs: globalStubs },
      });
      const cards = wrapper.findAll(".image-card");
      expect(cards.length).toBe(2);
    });

    it("shows 未命名 when title and filename are missing", () => {
      const modelValue = [{ uid: 1, url: "https://example.com/img.png" }];
      const wrapper = mount(ImageUploader, {
        props: { modelValue, showInfo: true },
        global: { stubs: globalStubs },
      });
      expect(wrapper.text()).toContain("未命名");
    });

    it("hides image info when showInfo is false", () => {
      const modelValue = [
        { uid: 1, url: "https://example.com/img.png", title: "Test" },
      ];
      const wrapper = mount(ImageUploader, {
        props: { modelValue, showInfo: false },
        global: { stubs: globalStubs },
      });
      expect(wrapper.find(".image-info").exists()).toBe(false);
    });
  });

  // ── Props ──────────────────────────────────────────────────

  describe("props", () => {
    it("accepts maxCount prop and applies it", () => {
      const wrapper = mount(ImageUploader, {
        props: { maxCount: 3 },
        global: { stubs: globalStubs },
      });
      expect(wrapper.props("maxCount")).toBe(3);
    });

    it("accepts custom uploadApi path", () => {
      const wrapper = mount(ImageUploader, {
        props: { uploadApi: "/custom/upload" },
        global: { stubs: globalStubs },
      });
      expect(wrapper.props("uploadApi")).toBe("/custom/upload");
    });
  });

  // ── File validation ────────────────────────────────────────

  describe("file validation", () => {
    it("rejects non-image file type", async () => {
      const wrapper = mount(ImageUploader, { global: { stubs: globalStubs } });
      const file = createFile("test.pdf", "application/pdf");
      const input = wrapper.find('input[type="file"]');
      Object.defineProperty(input.element, "files", {
        value: [file],
      });
      await input.trigger("change");
      expect(mockElMessageWarning).toHaveBeenCalledWith(
        expect.stringContaining("不是图片文件"),
      );
    });

    it("rejects oversized file", async () => {
      const wrapper = mount(ImageUploader, {
        props: { maxSize: 0.001 },
        global: { stubs: globalStubs },
      });
      const file = createFile("big.png", "image/png", 1024 * 10);
      const input = wrapper.find('input[type="file"]');
      Object.defineProperty(input.element, "files", {
        value: [file],
      });
      await input.trigger("change");
      expect(mockElMessageWarning).toHaveBeenCalledWith(
        expect.stringContaining("超过"),
      );
    });

    it("accepts valid image file", async () => {
      const mockRequest = (await import("@/utils/request")).default;
      mockRequest.post.mockResolvedValue({
        code: 200,
        data: {
          id: 99,
          storagePath: "https://cdn.example.com/uploaded.png",
          filename: "test.png",
          title: "test.png",
          fileSize: 1024,
          fileType: "image/png",
        },
      });

      const wrapper = mount(ImageUploader, { global: { stubs: globalStubs } });
      const file = createFile("test.png", "image/png", 512);
      const input = wrapper.find('input[type="file"]');
      Object.defineProperty(input.element, "files", {
        value: [file],
      });

      // Spy on imageList mutation after upload completes
      await input.trigger("change");
      await wrapper.vm.$nextTick();

      // The uploadFile is async - wait a bit for the mock to resolve
      await vi.waitFor(
        () => {
          const cards = wrapper.findAll(".image-card");
          expect(cards.length).toBe(1);
        },
        { timeout: 3000 },
      );
    });
  });

  // ── Delete ─────────────────────────────────────────────────

  describe("deleteImage", () => {
    it("removes image from list on delete", async () => {
      const modelValue = [
        { uid: 1, url: "https://example.com/img.png", title: "Test" },
      ];
      const wrapper = mount(ImageUploader, {
        props: { modelValue },
        global: { stubs: globalStubs },
      });

      // Click the delete button inside the image card
      const deleteBtn = wrapper.find(".delete-btn-inline");
      expect(deleteBtn.exists()).toBe(true);
      await deleteBtn.trigger("click");
      await wrapper.vm.$nextTick();

      // After delete, the image should be gone
      expect(wrapper.findAll(".image-card").length).toBe(0);
      expect(mockElMessageSuccess).toHaveBeenCalledWith("图片已删除");
    });

    it("emits update:modelValue after delete", async () => {
      const modelValue = [
        { uid: 1, url: "https://example.com/img.png", title: "Test" },
      ];
      const wrapper = mount(ImageUploader, {
        props: { modelValue },
        global: { stubs: globalStubs },
      });

      await wrapper.find(".delete-btn-inline").trigger("click");
      await wrapper.vm.$nextTick();
      expect(wrapper.emitted("update:modelValue")).toBeTruthy();
    });
  });

  // ── Drag and drop ──────────────────────────────────────────

  describe("drag and drop", () => {
    it("reorders images on drag", async () => {
      const modelValue = [
        { uid: 1, url: "https://example.com/a.png", title: "A" },
        { uid: 2, url: "https://example.com/b.png", title: "B" },
      ];
      const wrapper = mount(ImageUploader, {
        props: { modelValue },
        global: { stubs: globalStubs },
      });

      const cards = wrapper.findAll(".image-card");
      expect(cards.length).toBe(2);

      // Simulate dragStart on first card
      await cards[0].trigger("dragstart", {
        dataTransfer: {
          effectAllowed: "",
          setData: () => {},
        },
      });

      // Simulate dragEnter on second card
      await cards[1].trigger("dragenter", {
        preventDefault: () => {},
      });

      // Simulate dragEnd
      await cards[0].trigger("dragend");
      await wrapper.vm.$nextTick();

      // The modelValue should have been emitted after reorder
      expect(wrapper.emitted("update:modelValue")).toBeTruthy();
    });
  });

  // ── Upload errors ──────────────────────────────────────────

  describe("upload errors", () => {
    it("handles upload failure gracefully", async () => {
      const mockRequest = (await import("@/utils/request")).default;
      mockRequest.post.mockRejectedValue(new Error("Network error"));

      const wrapper = mount(ImageUploader, { global: { stubs: globalStubs } });
      const file = createFile("test.png", "image/png");
      const input = wrapper.find('input[type="file"]');
      Object.defineProperty(input.element, "files", {
        value: [file],
      });

      await input.trigger("change");

      await vi.waitFor(
        () => {
          expect(mockElMessageError).toHaveBeenCalled();
        },
        { timeout: 3000 },
      );
    });

    it("handles API error response", async () => {
      const mockRequest = (await import("@/utils/request")).default;
      mockRequest.post.mockResolvedValue({
        code: 500,
        message: "服务器错误",
      });

      const wrapper = mount(ImageUploader, { global: { stubs: globalStubs } });
      const file = createFile("test.png", "image/png");
      const input = wrapper.find('input[type="file"]');
      Object.defineProperty(input.element, "files", {
        value: [file],
      });

      await input.trigger("change");

      await vi.waitFor(
        () => {
          expect(mockElMessageError).toHaveBeenCalled();
        },
        { timeout: 3000 },
      );
    });
  });
});
