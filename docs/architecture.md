# Project Architecture

The Mario Kart 8 Deluxe Performance Analyzer is organized into three main application components:

1. Frontend
   - Built with Next.js, React, TypeScript, and Tailwind CSS.
   - Provides pages for video upload, results, and player performance tracking.
   - Communicates with the .NET Web API backend.

2. Backend
   - Built using .NET Web API.
   - Handles application logic, API requests, database communication, and communication with the video analysis service.
   - Uses Entity Framework Core to communicate with PostgreSQL.

3. Video Analysis Service
   - Built with Python.
   - Uses OpenCV to process Mario Kart gameplay videos and extract gameplay information.
   - Returns extracted data to the .NET backend.

4. Database
   - PostgreSQL is used to store users, races, tracks, performance results, and player comparisons.
   - PostgreSQL runs locally in a Docker container during development.

## Application Flow

User
→ Next.js Frontend
→ .NET Web API
→ Python Video Analysis Service

The .NET Web API also communicates with the PostgreSQL database to store and retrieve application data.

## Development Environment

Docker is used to run PostgreSQL locally.

The project will initially run locally during development.
