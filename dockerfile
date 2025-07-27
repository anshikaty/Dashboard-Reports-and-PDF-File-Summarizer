
# Base image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Install OS-level dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Streamlit environment settings
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS false
ENV STREAMLIT_SERVER_PORT 7860
ENV STREAMLIT_SERVER_ENABLECORS false

# Expose port
EXPOSE 7860

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
