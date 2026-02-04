FROM python:3.12-slim

# Node для Tailwind
RUN apt update && apt install -y nodejs npm

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build:css

RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "app.py"]