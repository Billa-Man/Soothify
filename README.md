# hacknyu-project

**Built with:** ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=Streamlit&logoColor=white) ![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=flat&logo=mongodb&logoColor=white) ![OpenAI](https://img.shields.io/badge/OpenAI-74aa9c?style=flat&logo=openai&logoColor=white)

**Contributors:** Rigved Shirvalkar, Om Thakur, Sohith Bandari (ROS)

# Introduction

Find the GitHub issues and repos you actually care about. No more endless scrolling.

**What it does:**

This bot helps you discover relevant GitHub repositories and issues through natural conversation. Just tell it what you're looking for, and it will fetch what matters.

**Features:**
- Suggests relevant repositories and issues based on the difficulty level.
- Understands natural language questions
- Remembers context from previous chats

# Screenshots

<!--
<table>
  <tr>
    <td><img src="screenshots/home_page.png"></td>
    <td><img src="screenshots/repo_explorer.png"></td>
  </tr>
  <tr>
    <td><img src="screenshots/issue_tracker.png"></td>
    <td><img src="screenshots/bookmarked_repos.png"></td>
  </tr>
</table>
-->

# Project Setup Guide
This guide will help you set up and run the project locally.

**Prerequisites:**

- Python 3.12
- Git
- An OpenAI API key

## Installation Steps
First, clone the repository
```
https://github.com/Billa-Man/hacknyu-project.git
cd <project-directory>
```

### 1. Virtual Environment Setup
Create and activate a Python virtual environment:
```
# Create virtual environment
python3 -m venv hacknyu

# Activate virtual environment
# For Unix/macOS
source hacknyu/bin/activate

# For Windows
# hacknyu\Scripts\activate
```

### 2. Environment Configuration
Create a `.env` file in the project root:
```
# Create .env file
touch .env
```
Open and add the following configuration to your .env file:
```
# OpenAI API Configuration
OPENAI_API_KEY=YOUR_OPENAI_API_KEY

# GitHub API Configuration
DATABASE_HOST=YOUR_MONGODB_DATABASE_HOST

# Database Configuration
DATABASE_NAME=YOUR_MONGODB_DATABASE_NAME
```
**Important:** Replace the placeholder values:

- YOUR_OPENAI_API_KEY: Your OpenAI API key from https://platform.openai.com
- YOUR_MONGODB_DATABASE_HOST: The hostname/address where your MongoDB database is hosted (e.g., localhost, mongodb://host:port, or a connection string)
- YOUR_MONGODB_DATABASE_NAME: The name of your MongoDB database that you want to connect to

**For security reasons:**
- Never commit the .env file to version control
- Keep your API keys and passwords secure
- Make sure .env is included in your .gitignore file

### 3. Dependencies Installation
Install all required packages:
```
pip install -r requirements.txt
```

# Usage
Simply run the following code in your project directory after activating the environment:
```
streamlit run Home.py
```
