# Use Python 3.10 slim image
FROM python:3.10-slim

# Update and install samtools (required for your app)
RUN apt-get update && apt-get install -y samtools && apt-get clean

# Set working directory inside container
WORKDIR /app

# Copy current directory (app files) into container's /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Streamlit default port
EXPOSE 8501

# Run the Streamlit app when container starts
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]

