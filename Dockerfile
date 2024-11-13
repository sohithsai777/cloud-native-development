# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 to match Cloud Run's default port
EXPOSE 8080

# Set the environment variable to tell Flask to run in production
ENV FLASK_ENV=production

# Command to run the Flask app on port 8080
CMD ["python", "app.py"]
