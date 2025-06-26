# FastAPI ComfyUI WebSocket Project

This project is a FastAPI web server that connects to ComfyUI via WebSocket to process images uploaded from a browser. The server handles image processing requests and returns the processed images back to the client for display.

## Project Structure

```
fastapi-comfyui-websocket
├── app
│   ├── main.py              # Entry point of the FastAPI application
│   ├── websocket.py         # Manages WebSocket connection to ComfyUI
│   ├── comfyui_client.py    # Client for connecting to ComfyUI via WebSocket
│   └── utils.py             # Utility functions for image processing
├── static
│   ├── index.html           # HTML page for client interface
│   └── app.js               # JavaScript code for handling image uploads
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd fastapi-comfyui-websocket
   ```

2. **Install dependencies:**
   It is recommended to use a virtual environment. You can create one using `venv` or `conda`.

   ```
   pip install -r requirements.txt
   ```

3. **Run the FastAPI application:**
   ```
   uvicorn app.main:app --reload
   ```

4. **Access the application:**
   Open your browser and navigate to `http://localhost:8000/static/index.html` to access the client interface.

## Usage Guidelines

- Use the file input on the HTML page to upload an image.
- The image will be sent to the server via WebSocket for processing.
- Once processed, the image will be displayed on the canvas in the browser.

## Dependencies

- FastAPI
- WebSocket libraries
- Any additional libraries required for image processing (to be specified in `requirements.txt`).

## License

This project is licensed under the MIT License. See the LICENSE file for more details.