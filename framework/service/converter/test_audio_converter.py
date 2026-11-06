"""测试音频转换服务"""

import asyncio
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from framework.service.converter.silk_converter_service import audio_converter_service


def test_ffmpeg_available():
    """测试 ffmpeg 是否可用"""
    print("=" * 50)
    print("测试 1: 检查 ffmpeg 是否可用")
    print("=" * 50)

    available = audio_converter_service.is_available()
    print(f"ffmpeg 可用: {available}")
    print(f"ffmpeg 路径: {audio_converter_service._ffmpeg_path}")

    if not available:
        print("\n❌ ffmpeg 不可用，请先安装 ffmpeg")
        print("   方法 1: 下载放到 framework/service/converter/ffmpeg/bin/ 目录")
        print("   方法 2: 安装到系统 PATH (winget install ffmpeg)")
        return False

    print("✅ ffmpeg 可用")
    return True


def test_convert_silk_to_mp3():
    """测试 silk 转 mp3"""
    print("\n" + "=" * 50)
    print("测试 2: silk 转 mp3")
    print("=" * 50)

    if not audio_converter_service.is_available():
        print("❌ 跳过：ffmpeg 不可用")
        return

    # 构造模拟的 silk 数据
    # 注意：真实的 silk 数据需要特定的编码，这里只是测试流程
    # 微信 silk 格式通常以 0x02 开头，后面是 #!SILK_V3

    # 模拟微信 silk 格式（带 0x02 头）
    # 实际上这只是测试数据，不会产生有效的音频
    mock_wechat_silk = bytes([0x02]) + b"#!SILK_V3" + b"\x00" * 100

    print(f"模拟微信 silk 数据大小: {len(mock_wechat_silk)} bytes")

    result = audio_converter_service.convert_silk_to_mp3(mock_wechat_silk)

    if result:
        print(f"✅ 转换成功，输出大小: {len(result)} bytes")
    else:
        print("⚠️ 转换返回空数据（模拟数据不是有效的 silk 音频，这是正常的）")


def test_convert_pcm_to_mp3():
    """测试 PCM 转 mp3（这个应该能成功）"""
    print("\n" + "=" * 50)
    print("测试 3: PCM 转 mp3（生成静音音频）")
    print("=" * 50)

    if not audio_converter_service.is_available():
        print("❌ 跳过：ffmpeg 不可用")
        return

    # 生成 1 秒的静音 PCM 数据
    # 采样率 24000, 单声道, 16bit = 24000 * 2 = 48000 bytes
    sample_rate = 24000
    duration_sec = 1
    pcm_data = b"\x00" * (sample_rate * 2 * duration_sec)

    print(f"生成静音 PCM 数据: {len(pcm_data)} bytes ({duration_sec}秒)")

    result = audio_converter_service.convert_to_mp3(pcm_data, "s16le")

    if result:
        print(f"✅ 转换成功，输出大小: {len(result)} bytes")

        # 保存测试文件
        test_dir = os.path.join(os.path.dirname(__file__), "test_output")
        os.makedirs(test_dir, exist_ok=True)
        test_file = os.path.join(test_dir, "test_silent.mp3")

        with open(test_file, "wb") as f:
            f.write(result)

        print(f"✅ 已保存测试文件: {test_file}")
        print("   可以用播放器打开验证")
    else:
        print("❌ 转换失败")


async def test_convert_url():
    """测试从 URL 下载并转换"""
    print("\n" + "=" * 50)
    print("测试 4: 从 URL 下载并转换")
    print("=" * 50)

    if not audio_converter_service.is_available():
        print("❌ 跳过：ffmpeg 不可用")
        return

    # 使用一个测试 URL（这里用一个假的 URL 测试错误处理）
    test_url = "https://example.com/test.silk"

    print(f"测试 URL: {test_url}")
    print("(预期会失败，因为 URL 不存在，这是测试错误处理)")

    result = await audio_converter_service.convert_silk_url_to_mp3(test_url)

    if result:
        print(f"转换成功: {len(result)} bytes")
    else:
        print("✅ 错误处理正常（URL 无效时返回空数据）")


def main():
    print("\n" + "=" * 60)
    print("音频转换服务测试")
    print("=" * 60)

    # 测试 1: ffmpeg 可用性
    if not test_ffmpeg_available():
        return

    # 测试 2: silk 转 mp3
    test_convert_silk_to_mp3()

    # 测试 3: PCM 转 mp3
    test_convert_pcm_to_mp3()

    # 测试 4: URL 下载
    asyncio.run(test_convert_url())

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
