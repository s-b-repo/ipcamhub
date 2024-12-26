IP Camera Dorking Tool
Introduction

Welcome to the IP Camera Dorking Tool — the only tool you'll ever need to scour the internet for IP camera URLs using Google Dorks. But wait, there's more! This isn't just any tool. It's unobfuscated, easy-to-read, and transparent (just like your search for vulnerable IP cameras should be).

Why obfuscate code when you can keep it clean, readable, and actually useful? If you're the type who obfuscates code for "security" reasons, then this tool probably isn't for you — unless you want to see a clear, understandable codebase and not one that looks like it was written in a secret language only decipherable by the most determined code detectives. But hey, we get it… obfuscating code makes you feel like a mysterious hacker. We see you.
Features

    Google Dorking: Use advanced search queries to find vulnerable IP cameras.
    Dynamic Rate Limiting: If you're hitting rate limits, we'll handle that for you with a nice 3-minute delay. No need to obfuscate your requests to avoid detection.
    Verbose Mode: Because who doesn't want to see exactly what's happening under the hood (in a separate terminal tab, of course)? We’re not hiding anything.
    Easy to Use: If you know how to copy-paste a command, you’re good to go.

Why This Tool Doesn't Obfuscate Itself

We know some of you like to add extra layers of "mystery" to your code. You know, the kind of mystery that involves renaming variables to things like a1, x4, or var10_999. But here’s the thing: obfuscation is for people who want to hide what they're doing. If you’re proud of your work (like we are), you shouldn’t need to obfuscate it.

This tool is 100% transparent. It's easy to understand, easy to extend, and easy to use. Don’t hide behind unnecessary tricks. Just because you can obfuscate code, doesn’t mean you should. We believe in writing code that even your grandmother could understand (well, as long as she's into network security).

Installation
Step 1: Set up a Virtual Environment

    First, navigate to the directory where you want to store the project:

cd /path/to/your/project

Create a virtual environment:

python3 -m venv venv

Activate the virtual environment:

    Linux/Mac:

source venv/bin/activate

Windows:

        .\venv\Scripts\activate

Step 2: Install Required Dependencies

Once your virtual environment is activated, install the necessary dependencies by running:

pip install requests beautifulsoup4 re time webbrowser json threading

For verbose mode or additional libraries, you might want to install subprocess if not already available (typically built into Python, but worth mentioning if you're having issues).
python ipcamdorking.py

It’s that simple. No need to hide the commands behind 50 lines of mangled variables. We respect your time.
Verbose Mode

Want to see what’s going on behind the scenes? Start the tool in verbose mode. We’ll open a new terminal tab for you to monitor what’s happening in real-time.
Dealing with Rate Limits

Google doesn’t like it when you send too many requests. Don’t worry — when we hit a rate limit, we’ll sleep for 3 minutes before trying again. No obfuscation, just straight-up honesty. You’ll even get a nice message telling you we’re waiting to avoid getting blocked.
