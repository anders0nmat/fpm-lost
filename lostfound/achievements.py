
from .models import Achievement, Client, Tracker
import logging
import datetime

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
    MODIFIERS = {
        '__minute': lambda x: x.minute,
        '__hour': lambda x: x.hour,
        '__day': lambda x: x.day,
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
        'timestamp',
    )
    
    for update in client.trackerupdate_set.all():
        for key, value in condition.items():
            kk = key.casefold()
            field, kk = next(((field, kk[len(field):]) for field in FIELDS if kk.startswith(field)), (None, kk))
            modifier, kk = next(((v, kk[len(k):]) for k, v in MODIFIERS.items() if kk.startswith(k)), (lambda x: x, kk))
            negate = kk.startswith('__not')
            if negate: kk = kk[len('__not'):]
            operator = OPERATORS.get(kk, None)

            if not field or not operator:
                # invalid condition
                logger.info(f'Invalid condition. {key=} {value=}')
                break

            try:
                fulfilled = operator(modifier(getattr(update, field)), value)
                if negate:
                    fulfilled = not fulfilled
                if not fulfilled:
                    break
            except:
                logger.info(f'Exception when checking condition. {key=} {value=} field={getattr(update, field)}')
                break
        else:
            # no break, therefore all conditions succeeded
            return True
    return False

@Achievement.handler
def trackerupdates_time(client: Client, condition: Any, **_):
    if not isinstance(condition, dict):
        return False
    
    n = condition.get('count')
    span = condition.get('duration')
    mode = condition.get('mode')
    different = condition.get('unique')

    if not isinstance(n, int) or not isinstance(span, str) or not mode in ('apart', 'within') or not isinstance(different, bool):
        return False
    
    hr, mn, sc, *_ = span.split(':') + ['0', '0', '0']
    span = datetime.timedelta(hours=int(hr), minutes=int(mn), seconds=int(sc))

    time_tracker = list(client.trackerupdate_set.order_by('timestamp').values_list('timestamp', 'tracker_id'))

    for i, (time, creator) in enumerate(time_tracker):
        progress = 0
        tracker_seen = {creator}
        start_time = time
        for time2, creator2 in time_tracker[i + 1:]:
            within_timespan = start_time + span > time2
            seen = creator2 in tracker_seen
            valid = not different or not seen
            if mode == 'within':
                if not within_timespan:
                    break # out of timespan
                if valid:
                    progress += 1
                    tracker_seen.add(creator2)
                    if progress >= n:
                        return True
            elif mode == 'apart':
                if valid and within_timespan:
                    break
                if valid:
                    progress += 1
                    tracker_seen.add(creator2)
                    start_time = time2
                    if progress >= n:
                        return True
                
    return False


