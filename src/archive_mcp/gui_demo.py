"""Small invented exports for the installed desktop demo."""
import json


def write_demo_sources(root):
    root.mkdir(parents=True)
    topics = [
        ('Garden journal', 'Could my next project be a garden journal?',
         'Track seedlings, watering dates and observations in a local garden journal.'),
        ('Research notebook', 'How could I search my NLP research notes?',
         'Start with keyword search and show source citations for each research note.'),
    ]
    claude = []
    chatgpt = []
    for index, (title, question, answer) in enumerate(topics):
        stamp = f'2026-01-0{index + 1}T12:00:00Z'
        claude.append({'uuid': f'demo-claude-{index}', 'name': f'Example: {title}',
                       'created_at': stamp, 'updated_at': stamp, 'chat_messages': [
                           {'uuid': f'demo-user-{index}', 'sender': 'human', 'text': question,
                            'created_at': stamp},
                           {'uuid': f'demo-answer-{index}', 'sender': 'assistant', 'text': answer,
                            'created_at': stamp}]})
        chatgpt.append({'id': f'demo-chatgpt-{index}', 'title': f'Example: {title} follow-up',
                        'create_time': 1767355200 + index * 86400,
                        'mapping': {
                            'question': {'parent': None, 'message': {'id': 'question',
                                'author': {'role': 'user'}, 'content': {'parts': [question]}}},
                            'answer': {'parent': 'question', 'message': {'id': 'answer',
                                'author': {'role': 'assistant'}, 'content': {'parts': [
                                    answer + ' Keep the first version small and test it with a few examples.']}}}}})
    for name, data in [('claude.json', claude), ('chatgpt.json', chatgpt)]:
        (root / name).write_text(json.dumps(data), encoding='utf-8')
