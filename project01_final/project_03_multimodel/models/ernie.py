import os,mimetypes,json,pathlib,time,base64
from openai import OpenAI
from utils.image_utils import encode_image
import subprocess
import tempfile


class ErnieEngine:
    def __init__(self):
        api_key = os.getenv('ERNIE_API_KEY')
        if not api_key:
            raise ValueError("ERNIE_API_KEY not set,or .env file not found.")
        base_url = os.getenv('ERNIE_BASE_URL')
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=3,
        )
        if not self.client:
            raise ValueError("self.client not set,or .env file not found.")

    def _format_history_for_api(self, history):
        openai_messages = []

        for msg_dict in history:
            role = msg_dict.get('role')
            raw_content = msg_dict.get('content')

            if not raw_content:
                continue

            # 处理纯文本
            if isinstance(raw_content, str):
                openai_messages.append({"role": role, "content": raw_content})
                continue

            # 处理列表内容
            if isinstance(raw_content, list):
                content_parts = []
                print(f"DEBUG: Processing list content with {len(raw_content)} items")

                for idx, item in enumerate(raw_content):
                    print(f"DEBUG: Item {idx}: {item}")
                    item_type = item.get("type")

                    # 1. 处理文本
                    if item_type == "text":
                        text_val = item.get("text", "").strip()
                        if text_val:
                            content_parts.append({"type": "text", "text": text_val})
                            print(f"DEBUG: Added text part: {text_val}")

                    # 2. 处理图片
                    elif item_type in ["file", "image","video"]:
                        # 处理嵌套的文件结构
                        if "file" in item and isinstance(item["file"], dict):
                            file_path = item["file"].get("path")
                            print(f"DEBUG: Found nested file structure with path: {file_path}")
                        else:
                            # 处理直接的路径结构
                            file_path = item.get("path")
                            print(f"DEBUG: Found direct file path: {file_path}")

                        if file_path:
                            normalized_path = os.path.normpath(file_path)
                            print(f"DEBUG: Normalized file path: {normalized_path}")

                            if os.path.exists(normalized_path):
                                print(f"DEBUG: File exists at: {normalized_path}")
                            else:
                                print(f"ERROR: File not found at path: {normalized_path}")
                                content_parts.append(
                                    {"type": "text", "text": f"[系统提示: 文件未找到 - {normalized_path}]"})
                                continue

                            try:
                                mime_type, _ = mimetypes.guess_type(file_path)

                                if mime_type and mime_type.startswith('image'):
                                    base64_str = encode_image(file_path)
                                    mime_type = mime_type or "image/jpeg"

                                    data_uri = f"data:{mime_type};base64,{base64_str}"

                                    content_parts.append({
                                        "type": "image_url",
                                        "image_url": {
                                            "url": data_uri
                                        }
                                    })
                                    print(f"DEBUG: Image encoded successfully: {file_path}")

                                elif mime_type and mime_type.startswith('video'):
                                    print(f"DEBUG: Processing video file: {file_path}")

                                    video_frames = self._extract_video_frames(file_path)
                                    print(f"DEBUG: Extracted {len(video_frames)} frames from video")

                                    for idx, frame_path in enumerate(video_frames):
                                        if os.path.exists(frame_path):
                                            base64_str = encode_image(frame_path)

                                            data_uri = f"data:image/jpeg;base64,{base64_str}"

                                            content_parts.append({
                                                "type": "image_url",
                                                "image_url": {
                                                    "url": data_uri
                                                }
                                            })
                                            print(f"DEBUG: Video frame {idx + 1} encoded successfully")

                                            os.unlink(frame_path)

                                    content_parts.append({
                                        "type": "text",
                                        "text": f"[视频已转换为 {len(video_frames)} 帧图片进行分析]\n{os.path.basename(file_path)} ({mime_type})"
                                    })
                                else:
                                    content_parts.append({
                                        "type": "text",
                                        "text": f"[上传了文件: {os.path.basename(file_path)} ({mime_type or 'unknown'})]"
                                    })
                                    print(f"DEBUG: File added: {file_path}")
                            except Exception as e:
                                print(f"ERROR processing file {file_path}: {e}")
                                content_parts.append({"type": "text", "text": f"[系统提示: 文件处理失败 - {str(e)}]"})

                if content_parts:
                    openai_messages.append({"role": role, "content": content_parts})
        return openai_messages

    def _extract_video_frames(self, video_path):
        frames = []
        temp_dir = tempfile.gettempdir()

        try:
            if not self._check_ffmpeg_installed():
                print("ERROR: ffmpeg not found. Please install ffmpeg first.")
                return frames

            duration = self._get_video_duration(video_path)
            print(f"DEBUG: Video duration: {duration:.2f}s")

            if duration < 10:
                num_frames = 10
            elif duration < 60:
                num_frames = 20
            else:
                num_frames = 30

            output_pattern = os.path.join(temp_dir, f"video_frame_%d.jpg")

            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vf", rf"select=eq(n\,0)+eq(n\,{num_frames})+between(t\,0\,{duration})",
                "-q:v", "2",
                "-vsync", "vfr",
                output_pattern
            ]

            print(f"DEBUG: Executing ffmpeg command: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"ERROR: ffmpeg command failed: {result.stderr}")
                return frames

            for i in range(1, num_frames + 1):
                frame_path = os.path.join(temp_dir, f"video_frame_{i}.jpg")
                if os.path.exists(frame_path):
                    frames.append(frame_path)
                    print(f"DEBUG: Found extracted frame: {frame_path}")

        except Exception as e:
            print(f"ERROR extracting video frames: {e}")
            for frame_path in frames:
                if os.path.exists(frame_path):
                    os.unlink(frame_path)
            frames = []

        return frames

    def _check_ffmpeg_installed(self):
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _get_video_duration(self, video_path):
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
            return 0.0
        except Exception as e:
            print(f"ERROR getting video duration: {e}")
            return 0.0

    def chat(self, history, model_name: str = "ernie-5.0-thinking-preview", temperature: float = 0.7,
             prompt_text: str = ""):
        # 1. 注入 System Prompt
        messages_payload = []
        if prompt_text and prompt_text.strip():
            messages_payload.append({"role": "system", "content": prompt_text.strip()})

        # 2. 格式化历史
        parsed_history = self._format_history_for_api(history)
        messages_payload.extend(parsed_history)

        # 3. 优化用户指令（针对图片识别场景）
        if messages_payload and isinstance(messages_payload[-1].get("content"), list):
            last_content = messages_payload[-1]["content"]
            has_image = any(item.get("type") == "image_url" for item in last_content)

            if has_image:
                for item in last_content:
                    if item.get("type") == "text":
                        original_text = item["text"]
                        if len(original_text.strip()) < 20 and ("识别" in original_text or "提取" in original_text):
                            item["text"] = f"{original_text} 请详细描述图片中的内容，包括人物、物体、场景等细节。"
                            print(f"DEBUG: Enhanced text prompt to: {item['text']}")

        debug_payload = json.dumps(messages_payload, ensure_ascii=False)
        print(f"DEBUG: Payload sending to API (truncated): {debug_payload[:500]} ... [len: {len(debug_payload)}]")

        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages_payload,
                temperature=temperature,
                max_tokens=2048,
                top_p=0.9,
                stream=True,
            )

            history.append({"role": "assistant", "content": ""})

            print(f"DEBUG: Starting to receive API response chunks...")
            response_received = False

            for chunk_idx, chunk in enumerate(response):
                print(f"DEBUG: Received chunk {chunk_idx}: {chunk}")
                response_received = True

                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        history[-1]["content"] += delta.content
                        print(f"DEBUG: Appended content: {delta.content}")
                        yield history

            if not response_received:
                print(f"WARNING: No response chunks received from API")
                history[-1]["content"] = "API未返回有效响应"
                yield history
            else:
                print(f"DEBUG: API response completed successfully")

        except Exception as e:
            print(f"Ernie API Error: {e}")
            if not history or history[-1]["role"] != "assistant":
                history.append({"role": "assistant", "content": ""})
            history[-1]["content"] += f"\n[API 调用错误: {str(e)}]"
            yield history

