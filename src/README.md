# Mergington High School Activities API

A FastAPI application for viewing extracurricular activities, teacher authentication, and database-backed announcements.

## Features

- View all available extracurricular activities
- Sign up and unregister students from activities (teachers only)
- Manage school announcements with start and expiration dates (signed-in users only)

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/activities` | Get all activities with optional day/time filtering |
| GET | `/activities/days` | Get all available activity days |
| POST | `/activities/{activity_name}/signup?email=student@mergington.edu&teacher_username=<teacher>` | Sign up a student for an activity |
| POST | `/activities/{activity_name}/unregister?email=student@mergington.edu&teacher_username=<teacher>` | Unregister a student from an activity |
| POST | `/auth/login?username=<teacher>&password=<password>` | Sign in as teacher/admin |
| GET | `/auth/check-session?username=<teacher>` | Validate a signed-in teacher session |
| GET | `/announcements?active_only=true` | Get active announcements for banner display |
| GET | `/announcements?active_only=false` | Get all announcements for management |
| POST | `/announcements?teacher_username=<teacher>` | Create an announcement |
| PUT | `/announcements/{announcement_id}?teacher_username=<teacher>` | Update an announcement |
| DELETE | `/announcements/{announcement_id}?teacher_username=<teacher>` | Delete an announcement |

## Data Model

The application uses MongoDB collections with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Teachers** - Uses username as identifier:
   - Display name
   - Argon2 password hash
   - Role

3. **Announcements**
   - Title
   - Message
   - Optional start date
   - Required expiration date

Initial sample data is loaded from `src/backend/database.py` when collections are empty.
