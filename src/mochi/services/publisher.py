"""Publishing service — upload to YouTube, TikTok, Instagram."""

from __future__ import annotations

from pathlib import Path

from mochi.models.script import Script


async def upload_youtube(
    video_path: Path,
    script: Script,
    config: dict,
) -> str:
    """Upload video to YouTube via the Data API v3.

    Returns the video URL.
    """
    # TODO: Implement YouTube upload via google-api-python-client
    # Requires OAuth2 setup (one-time interactive flow)
    #
    # from googleapiclient.discovery import build
    # from googleapiclient.http import MediaFileUpload
    #
    # youtube = build("youtube", "v3", credentials=creds)
    # request = youtube.videos().insert(
    #     part="snippet,status",
    #     body={
    #         "snippet": {
    #             "title": script.title,
    #             "description": script.description,
    #             "tags": list(script.hashtags),
    #             "categoryId": "27",  # Education
    #         },
    #         "status": {
    #             "privacyStatus": "public",
    #             "selfDeclaredMadeForKids": False,
    #         },
    #     },
    #     media_body=MediaFileUpload(str(video_path)),
    # )
    # response = request.execute()
    # return f"https://youtube.com/watch?v={response['id']}"

    print(f"[YouTube] Would upload: {video_path}")
    print(f"  Title: {script.title}")
    print(f"  Tags: {', '.join(script.hashtags)}")
    return f"https://youtube.com/watch?v=PLACEHOLDER"


async def upload_tiktok(
    video_path: Path,
    script: Script,
    config: dict,
) -> str:
    """Upload video to TikTok via Content Posting API.

    Returns the video URL.
    """
    # TODO: Implement TikTok upload via their Content Posting API
    # Requires app approval and OAuth2

    caption = f"{script.hook}\n\n{' '.join(f'#{h}' for h in script.hashtags)}"
    print(f"[TikTok] Would upload: {video_path}")
    print(f"  Caption: {caption}")
    return "https://tiktok.com/@mochi/video/PLACEHOLDER"


async def upload_instagram(
    video_path: Path,
    script: Script,
    config: dict,
) -> str:
    """Upload video to Instagram Reels via Graph API.

    Returns the post URL.
    """
    # TODO: Implement Instagram Reels upload via Graph API
    # Requires Facebook Business account and app review

    caption = f"{script.hook}\n\n{' '.join(f'#{h}' for h in script.hashtags)}"
    print(f"[Instagram] Would upload: {video_path}")
    print(f"  Caption: {caption}")
    return "https://instagram.com/reel/PLACEHOLDER"


async def publish_all(
    video_path: Path,
    script: Script,
    config: dict,
    platforms: list[str] | None = None,
) -> dict[str, str]:
    """Publish video to all configured platforms.

    Returns a dict of platform -> URL.
    """
    if platforms is None:
        platforms = ["youtube"]

    results: dict[str, str] = {}

    uploaders = {
        "youtube": upload_youtube,
        "tiktok": upload_tiktok,
        "instagram": upload_instagram,
    }

    for platform in platforms:
        uploader = uploaders.get(platform)
        if uploader is None:
            print(f"[Warning] Unknown platform: {platform}")
            continue
        url = await uploader(video_path, script, config)
        results[platform] = url

    return results
