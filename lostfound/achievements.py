
from .models import Achievement, Client, Tracker
import logging

import re

logger = logging.Logger('lostfound')

@Achievement.handler
def found_all_trackers(client: Client, condition, **_) -> tuple[int, int]:
    if condition == '__all__':
        condition = list(Tracker.objects.values_list('tag', flat=True))
    if isinstance(condition, str):
        condition = [condition]
    if not isinstance(condition, list):
        return False
    
    found_trackers = set(tag.casefold() for tag in client.trackers.all().values_list('tag', flat=True))
    all_trackers = set(tag.casefold() for tag in condition)
    return len(found_trackers & all_trackers), len(all_trackers)

@Achievement.handler
def found_any_trackers(client: Client, condition, **_) -> tuple[int, int]:
    if condition == '__all__':
        condition = list(Tracker.objects.values_list('tag', flat=True))
    if not isinstance(condition, list):
        return False
    
    found_trackers = set(tag.casefold() for tag in client.trackers.all().values_list('tag', flat=True))
    all_trackers = set(tag.casefold() for tag in condition)
    return len(found_trackers & all_trackers) > 0

@Achievement.handler
def tried_tracker(client: Client, condition, form_value, **_):
    if not isinstance(form_value, str):
        return False
    if not isinstance(condition, str):
        return False
    
    return form_value.casefold() == condition.casefold()

@Achievement.handler
def trackerupdate_matches(client: Client, condition: dict[str, Any], **_):
    if not isinstance(condition, dict):
        return False
    
    OPERATORS = {
        '__<': lambda x, a: x < a,
        '__>': lambda x, a: x > a,
        '__=': lambda x, a: x == a,
        '__in': lambda x, a: x in a,
        '__matches': lambda x, a: re.search(a, x) is not None,
        '__range': lambda x, a: a[0] <= x <= a[1],
    }
    FIELDS = (
        'latitude',
        'longitude',
        'accuracy',
        'altitude',
        'altitude_accuracy',
        'speed',
        'heading',
        'message',
        'picture',
    )
    
    for update in client.trackerupdate_set.all():
        for key, value in condition.items():
            field = next((field for field in FIELDS if key.casefold().startswith(field)), None)
            operator = OPERATORS.get(key[len(field):], None)

            if not field or not operator:
                # invalid condition
                logger.info(f'Invalid condition. {key=} {value=}')
                break

            try:
                if not operator(getattr(update, field), value):
                    break
            except:
                logger.info(f'Exception when checking condition. {key=} {value=} field={getattr(update, field)}')
                break
        else:
            # no break, therefore all conditions succeeded
            return True
    return False

