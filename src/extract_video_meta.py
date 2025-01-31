
import subprocess
import json

def extract_all_video_metadata(video_path):
    try:
        # Run ffprobe to get all metadata
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-print_format', 'json', '-show_format', '-show_streams', '-show_entries', 'frame', '-show_programs', '-show_chapters', '-show_private_data', '-show_packets', video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Parse the JSON output
        metadata = json.loads(result.stdout)

        return metadata

    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return None

# Example usage:
video_path = '/Users/dean/Downloads/testVideo/DJI_0004.MP4'
metadata = extract_all_video_metadata(video_path)

# Print all metadata in a readable JSON format
if metadata:
    print(json.dumps(metadata, indent=4))