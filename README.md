# Face Recognition Attendance System

## Overview

A real-time attendance management system that automates student attendance using computer vision and machine learning. The system captures student faces through a webcam, identifies registered students using K-Nearest Neighbors (KNN), and automatically records attendance in a database.

## Features

* Real-time face detection and recognition
* Student registration and face dataset creation
* KNN-based face classification
* Automated attendance marking
* SQLite database integration
* Student profile management
* Attendance history tracking
* GUI-based workflow

## Tech Stack

### Languages

* Python

### Libraries

* OpenCV
* NumPy
* Scikit-learn

### Database

* SQLite

## System Workflow

1. Register student information
2. Capture face samples
3. Train recognition model
4. Perform live face recognition
5. Automatically record attendance
6. Store attendance data in SQLite

## Key Achievements

* Built a complete attendance automation pipeline using computer vision and machine learning.
* Implemented modular architecture separating registration, training, and attendance tracking.
* Integrated SQLite for efficient student profile and attendance management.
* Reduced manual attendance effort through real-time recognition.

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
python attendance.py
```
