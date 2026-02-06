FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Java (required for terraform_metrics JAR)
RUN apt-get update && \
    apt-get install -y default-jre-headless git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Install the package
RUN pip install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
ENTRYPOINT ["tf-metrics"]
CMD ["--help"]
