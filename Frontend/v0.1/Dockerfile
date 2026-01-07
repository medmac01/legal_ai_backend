# Use official Python slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose default Streamlit port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "chat.py", "--server.address=0.0.0.0"]