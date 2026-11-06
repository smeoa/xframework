"""附件规则（表单提交与上传接口共用）"""

ATTACHMENT_RULES: dict[str, dict] = {
    "F03": {"extensions": {"jpg", "jpeg", "png", "pdf", "step", "stl"}, "max_mb": 10, "max_count": 5},
    "F04": {"extensions": {"ai", "png", "pdf"}, "max_mb": 10, "max_count": 5},
    "F05": {"extensions": {"pdf", "jpg", "jpeg", "png"}, "max_mb": 5, "max_count": 1},
    "F06": {"extensions": {"jpg", "jpeg", "png", "pdf", "step", "stl"}, "max_mb": 10, "max_count": 5},
}
