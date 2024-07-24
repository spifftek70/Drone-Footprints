from quart import Quart, request, jsonify
from Utils.logger_config import init_logger, startup, end_logger
from loguru import logger
import asyncio
import sys

app = Quart(__name__)

@app.before_serving
async def before_serving():
    # Ensure WebSocket servers are started and logger is initialized
    await startup()

@app.route('/run_script', methods=['POST'])
async def run_script():
    data = await request.get_json()
    outer_path = data['outputPath']
    file_handler_id = init_logger(outer_path)  # Initialize logger with path for log files
    logger.info(f"Received payload: {data}")

    # Construct command line arguments based on the received data
    args = ["python", "/usr/src/app/Drone_Footprints.py", "-o", str(outer_path), "-i", data['inputPath']]
    for flag, arg in [('-d', 'declination'), ('-c', 'cog'), ('-l', 'lense_correction'), ('-z', 'image_equalize'),
                      ('-v', 'dsmFile'), ('-m', 'elevation_service'), ('-e', 'epsg'), ('-w', 'sensorWidth'), ('-t', 'sensorHeight'),
                      ('-n', 'nodejs'), ('-y', 'not_nodejs')]:
        if data.get(arg):
            args.append(flag)
            if arg in ['dsmFile', 'sensorWidth', 'sensorHeight', 'epsg']:
                args.append(str(data[arg]))

    # Execute the command and handle subprocess output
    process = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        bufsize=0  # Set buffering to unbuffered
    )
    stdout = process.stdout
    stderr = process.stderr
    async for line in process.stdout:
        # Handle output line by line
        logger.info(line.decode().strip())  # Log output

    # Read from stdout and stderr
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        logger.error(f"Error occurred while processing: {stderr.decode()}")
        end_logger(file_handler_id)
        return jsonify({'status': 'error', 'message': stderr.decode()}), 500

    logger.info(f"Processing complete: {stdout.decode()}")
    end_logger(file_handler_id)
    return jsonify({'status': 'success', 'message': stdout.decode()})
