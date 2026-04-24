from django.shortcuts import render
from django.http import JsonResponse
import json
import os
from django.conf import settings


# Load responses from JSON file
def load_responses():
    json_path = os.path.join(settings.BASE_DIR, 'chatbot', 'data', 'responses.json')
    with open(json_path, 'r', encoding='utf-8') as file:
        return json.load(file)


# Load data once when module loads
DATA = load_responses()
RESPONSES = DATA['responses']
FALLBACK_MESSAGE = DATA['fallback_message']
GREETINGS = DATA['greetings']
GREETING_RESPONSE = DATA['greeting_response']
THANKS = DATA['thanks']
THANKS_RESPONSE = DATA['thanks_response']
SUGGESTED_QUESTIONS = DATA['suggested_questions']


def get_bot_response(user_message):
    """
    Enhanced rule-based function to match user message with responses
    """
    # Convert to lowercase for case-insensitive matching
    user_message_lower = user_message.lower().strip()

    # Check for greetings first
    for greeting in GREETINGS:
        if greeting in user_message_lower:
            return GREETING_RESPONSE

    # Check for thanks
    for thank in THANKS:
        if thank in user_message_lower:
            return THANKS_RESPONSE

    # Check each intent's keywords
    best_match = None
    max_keywords_matched = 0

    for intent in RESPONSES:
        keywords_matched = 0
        for keyword in intent['keywords']:
            if keyword in user_message_lower:
                keywords_matched += 1

        # If we found a match with more keywords than previous best
        if keywords_matched > max_keywords_matched:
            max_keywords_matched = keywords_matched
            best_match = intent['response']

    # Return best match if found (and at least 1 keyword matched)
    if best_match and max_keywords_matched > 0:
        return best_match

    # If no match found, return fallback message
    return FALLBACK_MESSAGE


def chat_view(request):
    """
    Main view to display the chat interface
    """
    # Initialize chat history in session if it doesn't exist
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []

        # Add welcome message for new sessions
        welcome_message = "Hello! 👋 I'm your router support assistant. How can I help you with your Huawei A5 or V5 router today?"
        request.session['chat_history'].append({'type': 'bot', 'text': welcome_message})
        request.session.modified = True

    context = {
        'suggested_questions': SUGGESTED_QUESTIONS,
        'chat_history': request.session['chat_history']
    }
    return render(request, 'chat.html', context)


def get_response(request):
    """
    AJAX view to handle message sending and get bot response
    """
    if request.method == 'POST':
        try:
            # Get user message from POST data
            data = json.loads(request.body)
            user_message = data.get('message', '')

            if not user_message.strip():
                return JsonResponse({
                    'response': "Please type a message!",
                    'success': True
                })

            # Get bot response
            bot_response = get_bot_response(user_message)

            # Update chat history in session
            if 'chat_history' not in request.session:
                request.session['chat_history'] = []

            # Add messages to history
            chat_history = request.session['chat_history']
            chat_history.append({'type': 'user', 'text': user_message})
            chat_history.append({'type': 'bot', 'text': bot_response})

            # Keep only last 30 messages to prevent session from getting too large
            if len(chat_history) > 30:
                chat_history = chat_history[-30:]

            request.session['chat_history'] = chat_history
            request.session.modified = True

            # Return bot response as JSON
            return JsonResponse({
                'response': bot_response,
                'success': True
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=405)


def contact_view(request):
    return render(request, 'contact.html')


def clear_history(request):
    """
    Optional view to clear chat history
    """
    if 'chat_history' in request.session:
        del request.session['chat_history']
    return JsonResponse({'success': True})
