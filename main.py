from math import ceil, floor

import arrow
from notion.client import NotionClient
from notion.collection import NotionDate
from requests import HTTPError


def get_filters(date, repeat):
    filter_is_in_past = {
        'filter': {
            'value': {
                'type': 'relative',
                'value': 'today'
            },
            'operator': 'date_is_before'
        },
        'property': date
    }

    filter_is_after_1900 = {
        'filter': {
            'value': {
                'type': 'exact',
                'value': {
                    'start_date': '1901-01-01',
                    'type': 'date'
                }
            },
            'operator': 'date_is_after'
        },
        'property': date
    }

    filter_has_repeat = {
        'filter': {
            'operator': 'is_not_empty'
        },
        'property': repeat
    }

    filter_has_date = {
        'filter': {
            'operator': 'is_not_empty'
        },
        'property': date
    }

    return {
        'filters': [
            filter_has_date,
            filter_is_in_past,
            filter_is_after_1900,
            filter_has_repeat,
        ],
        'operator': 'and'
    }


error_messages = {
    'old_date': 'Please enter a date after January 1st, 1900 00:00:00 in Notion.',
    'repeat_frequency__zero': 'Please enter a custom repeat frequency greater than 0 in Notion.',
    'repeat_frequency_not_set': 'Please enter a custom repeat frequency in Notion.',
    'repeat_frequency_non_integer': 'Please enter an integral custom repeat frequency in Notion.',
    'invalid_option': 'Invalid option selected in Notion',
    'req_missing_db_address': 'URL missing database address',
    'req_missing_token': 'URL missing notion_token',
    'col_date_missing': 'Date column name missing from request URL',
    'col_repeat_missing': 'Repeat type column name missing from request URL',
    'col_frequency_missing': 'Custom Repeat Frequency column name missing from request URL',
    'invalid_token': 'User token is invalid. Maybe you were logged out? <a href=""> How to get a token</a>',
    'invalid_database': 'Database is invalid.',
    'property_not_found': 'property not found: ',
    'timezone_missing': 'URL missing timezone',
}

errors = []
updated_records = 0


def update(notion_token, database_address, timezone, prop_date="Date", prop_repeat="Repeats",
           prop_repeat_frequency="RepeatFrequency"):
    global updated_records
    try:
        client = NotionClient(token_v2=notion_token)
    except HTTPError:
        errors.append(error_messages['invalid_token'])
        return False

    # noinspection PyBroadException
    try:
        database = client.get_collection_view("https://www.notion.so/" + database_address)
    except Exception:
        errors.append(error_messages['invalid_database_address'])
        return False

    props = database.collection.get_schema_properties()
    valid_props = True
    date_found = False
    repeat_found = False
    freq_found = False
    for prop in props:
        if not prop['name']:
            continue
        if prop['name'] == prop_date:
            date_found = True
        if prop['name'] == prop_repeat:
            repeat_found = True
        if prop['name'] == prop_repeat_frequency:
            freq_found = True

    if not date_found:
        errors.append("Date " + error_messages['property_not_found'] + prop_date)
        valid_props = False
    if not repeat_found:
        errors.append("Repeat " + error_messages['property_not_found'] + prop_repeat)
        valid_props = False
    if not freq_found:
        errors.append("Frequency " + error_messages['property_not_found'] + prop_repeat_frequency)
        valid_props = False

    if not valid_props:
        return False

    query_results = database.build_query(filter=get_filters(prop_date, prop_repeat)).execute()

    if query_results is None:
        return False
    for row in query_results:
        row_date = row.get_property(prop_date)
        row_repeats = row.get_property(prop_repeat)
        m_tz = row_date.timezone if row_date.timezone else timezone
        if row_date and row_repeats and (
                arrow.get(row_date.start, m_tz) < (
                arrow.now(m_tz))) and (
                row_repeats != "Does Not Repeat") \
                and ((arrow.get(row_date.end, m_tz) < (
                arrow.now(m_tz))) if row_date.end else True):

            new_time = arrow.get(row_date.start, m_tz)
            if row_date.end:
                new_end = arrow.get(row_date.end, m_tz)
            else:
                new_end = None

            success = True
            while new_time < (arrow.now(m_tz)):
                if row_repeats == "Daily":
                    v = ceil((arrow.now(m_tz) - new_time).days) + 1
                    new_time = new_time.shift(days=v)
                    if row_date.end:
                        new_end = new_end.shift(days=v)
                elif row_repeats == "Weekly":
                    v = ceil((arrow.now(m_tz) - new_time).days / 7)
                    new_time = new_time.shift(weeks=v)
                    if row_date.end:
                        new_end = new_end.shift(weeks=v)
                elif row_repeats == "Biweekly":
                    v = ceil((arrow.now(m_tz) - new_time).days / 14)
                    new_time = new_time.shift(weeks=v)
                    if row_date.end:
                        new_end = new_end.shift(weeks=v)
                elif row_repeats == "Monthly":
                    new_time = new_time.shift(months=1)
                    if row_date.end:
                        new_end = new_end.shift(months=1)
                elif row_repeats == "Bimonthly":
                    new_time = new_time.shift(months=2)
                    if row_date.end:
                        new_end = new_end.shift(months=2)
                elif row_repeats == "Quarterly":
                    new_time = new_time.shift(months=3)
                    if row_date.end:
                        new_end = new_end.shift(months=3)
                elif row_repeats == "Biannually":
                    new_time = new_time.shift(months=6)
                    if row_date.end:
                        new_end = new_end.shift(months=6)
                elif row_repeats == "Annually":
                    new_time = new_time.shift(months=12)
                    if row_date.end:
                        new_end = new_end.shift(months=12)
                elif row_repeats == "Biennially":
                    new_time = new_time.shift(months=24)
                    if row_date.end:
                        new_end = new_end.shift(months=24)
                elif row_repeats == "Custom":
                    if row.get_property(prop_repeat_frequency):
                        row_repeat_frequency = row.get_property(prop_repeat_frequency)
                        if not isinstance(row_repeat_frequency, int):
                            success = False
                            errors.append(error_messages['repeat_frequency_non_integer'])
                            break
                        if row_repeat_frequency > 0:
                            t = (arrow.now(m_tz) - new_time).days / row_repeat_frequency
                            new_time = new_time.shift(
                                days=floor(t) * row_repeat_frequency if t >= 1 else row_repeat_frequency)
                        else:
                            success = False
                            errors.append(error_messages['repeat_frequency_zero'])
                            break
                    else:
                        success = False
                        errors.append(error_messages['repeat_frequency_not_set'])
                        break
                else:
                    success = False
                    errors.append(error_messages['invalid_option'] + " '" + row_repeats + "'")
                    break

            if success:
                updated_records += 1
                if ":" in row_date.start.__str__():
                    if row_date.end:
                        notion_date = NotionDate(start=new_time.datetime, timezone=row_date.timezone,
                                                 end=new_end.datetime, reminder=row_date.reminder)
                    else:
                        notion_date = NotionDate(start=new_time.datetime, timezone=row_date.timezone,
                                                 reminder=row_date.reminder)
                    row.set_property(prop_date, notion_date)
                else:
                    if row_date.end:
                        notion_date = NotionDate(start=new_time.date(),
                                                 end=new_end.date(), reminder=row_date.reminder)
                    else:
                        notion_date = NotionDate(start=new_time.date(), reminder=row_date.reminder)

                    row.set_property(prop_date, notion_date)
    return True


def response_styling():
    return "<style>" \
           ".error { color: red;  display: block; font-size: 1.25em;} " \
           ".message { color: black;  display: block; font-size: 1.5em;}" \
           ".info { color:black; font-size: 1em; display: block; }" \
           ".res {" \
           "display: block;" \
           "margin: 0 auto;" \
           "}</style>"


def format_response(message):
    print("Errors: " + len(errors).__str__())
    global updated_records
    body = "<div class='res'><span class='message'>" + message + "</span>"
    body += "<span class='info'>Updated " + updated_records.__str__() + " records.</span>"
    if len(errors) > 0:
        for error in errors:
            print(error)
            body += "<span class='error'>" + error + "</span>"
    res = "<html><head>" + response_styling() + "</head><body>" + body + "</div></body></html>"
    errors.clear()
    updated_records = 0
    return res


def enter(request):
    good_request = True
    if request.args:
        if 'notion_token' not in request.args:
            errors.append(error_messages['req_missing_token'])
            good_request = False
        if 'database' not in request.args:
            errors.append(error_messages['req_missing_db_address'])
            good_request = False
        if 'date' not in request.args:
            errors.append(error_messages['col_date_missing'])
            good_request = False
        if 'repeat' not in request.args:
            errors.append(error_messages['col_repeat_missing'])
            good_request = False
        if 'frequency' not in request.args:
            errors.append(error_messages['col_frequency_missing'])
            good_request = False
        if 'timezone' not in request.args:
            errors.append(error_messages['timezone_missing'])
            good_request = False

    if good_request:
        if update(request.args['notion_token'], request.args['database'], request.args['timezone'],
                  prop_date=request.args['date'], prop_repeat=request.args['repeat'],
                  prop_repeat_frequency=request.args['frequency']):
            report()
            if len(errors) > 0:
                return format_response("Success, but some errors occurred...")
            else:
                return format_response("Success!")
        else:
            return format_response("Fatal error.")
    else:
        return format_response("Bad request.")


def report():
    print("Updated " + updated_records.__str__() + " records with " + len(errors).__str__() + " errors.")
