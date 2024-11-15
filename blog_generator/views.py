from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json
import os
from pytube import YouTube
import assemblyai as aai
import openai

# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data['link']
            # Validate YouTube link format
            if 'youtube.com' not in yt_link and 'youtu.be' not in yt_link:
                return JsonResponse({'error': 'Invalid YouTube link'}, status=400)
            
            # Get YouTube title and transcription
            title = get_yt_title(yt_link)
            transcription = get_transcription(yt_link)
            if not transcription:
                return JsonResponse({'error': "Failed to get transcript"}, status=500)

            # Generate blog content
            blog_content = generate_blog_from_transcription(transcription)
            if not blog_content:
                return JsonResponse({'error': "Failed to generate blog article"}, status=500)

            # Save blog to database (uncomment if model exists)
            # new_blog_article = BlogPost.objects.create(
            #     user=request.user,
            #     youtube_title=title,
            #     youtube_link=yt_link,
            #     generated_content=blog_content,
            # )
            # new_blog_article.save()

            return JsonResponse({'content': blog_content})
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data sent'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def get_yt_title(link):
    try:
        yt = YouTube(link)
        return yt.title
    except Exception as e:
        print(f"Error fetching YouTube title: {e}")
        return None

def download_audio(link):
    try:
        yt = YouTube(link)
        audio_stream = yt.streams.filter(only_audio=True).first()
        audio_file = audio_stream.download(output_path=settings.MEDIA_ROOT)
        return audio_file
    except Exception as e:
        print(f"Error downloading audio: {e}")
        return None

def get_transcription(link):
    audio_file = download_audio(link)
    if not audio_file:
        return None
    
    aai.settings.api_key = "your-assemblyai-api-key"
    transcriber = aai.Transcriber()
    try:
        transcript = transcriber.transcribe(audio_file)
        return transcript.text
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None

def generate_blog_from_transcription(transcription):
    openai.api_key = "your-openai-api-key"
    prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article:\n\n{transcription}\n\nArticle:"

    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=1000
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error generating blog content: {e}")
        return None

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = "Invalid username or password"
            return render(request, 'login.html', {'error_message': error_message})
        
    return render(request, 'login.html')

def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']

        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'Error creating account'
                return render(request, 'signup.html', {'error_message': error_message})
        else:
            error_message = 'Passwords do not match'
            return render(request, 'signup.html', {'error_message': error_message})
        
    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    return redirect('/')
