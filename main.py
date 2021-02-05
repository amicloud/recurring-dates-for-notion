from notion.client import NotionClient
from notion.collection import Collection
from notion.collection import Record
from notion.collection import NotionDate
import datetime
import arrow
from math import ceil
from dateutil import tz

api_token = "a247c56da33e1f0c72a39f2b38375c12d0defd1c3a99e0c1670861f02be1ead18dec679cc8774be70f2f0ded470d8807dc96f569ba1dc2500d843fab6500771918f8a200b0bd002edf9678d702ac"
client = NotionClient(token_v2=api_token)


def main():
    dataspace_do_url = "https://www.notion.so/94bd3b13c22e435eac539f308302239b?v=56c6c8e9b0e8468a9bf20bb8ee8e148d"
    dataspace_do_page = client.get_block(dataspace_do_url)
    dataspace_do = client.get_collection_view(dataspace_do_url)
    rows = dataspace_do.collection.get_rows()
    print(dataspace_do_page.title)

    for row in rows:
        if row.Date and row.Repeats and (
                arrow.get(row.Date.start) < (arrow.now(row.Date.timezone) if row.Date.timezone else arrow.now())) and (
                row.Repeats != "Does Not Repeat") \
                and ((arrow.get(row.Date.end) < (
                arrow.now(row.Date.timezone) if row.Date.timezone else arrow.now())) if row.Date.end else True):
            if arrow.get(row.Date.start) < arrow.get("1900-01-01 00:00:00"):
                row.set_property("Date", arrow.get("1900-01-01 00:00:00").datetime)
                break
            if row.Date.timezone:
                new_time = arrow.get(row.Date.start, tz.gettz(row.Date.timezone))
                if row.Date.end:
                    new_end = arrow.get(row.Date.end, tz.gettz(row.Date.timezone))

            else:
                new_time = arrow.get(row.Date.start)
                if row.Date.end:
                    new_end = arrow.get(row.Date.end)

            print(row.Date.start)
            fail = False

            while new_time < (arrow.now(row.Date.timezone) if row.Date.timezone else arrow.now()):
                if row.Repeats == "Daily":
                    v = ceil((arrow.now() - new_time).days) + 1
                    new_time = new_time.shift(days=v)
                    if row.Date.end:
                        new_end = new_end.shift(days=v)
                elif row.Repeats == "Weekly":
                    t = (arrow.now() - new_time).days / 7
                    v = t if t > 0 else 1
                    new_time = new_time.shift(weeks=v)
                    if row.Date.end:
                        new_end = new_end.shift(weeks=v)
                elif row.Repeats == "Biweekly":
                    t = (arrow.now() - new_time).days / 14
                    v = t if t > 0 else 2
                    new_time = new_time.shift(weeks=v)
                    if row.Date.end:
                        new_end = new_end.shift(weeks=v)
                elif row.Repeats == "Monthly":
                    new_time = new_time.shift(months=1)
                    if row.Date.end:
                        new_end = new_end.shift(months=1)
                elif row.Repeats == "Bimonthly":
                    new_time = new_time.shift(months=2)
                    if row.Date.end:
                        new_end = new_end.shift(months=2)
                elif row.Repeats == "Quarterly":
                    new_time = new_time.shift(months=3)
                    if row.Date.end:
                        new_end = new_end.shift(months=3)
                elif row.Repeats == "Biennially":
                    new_time = new_time.shift(months=6)
                    if row.Date.end:
                        new_end = new_end.shift(months=6)
                elif row.Repeats == "Annually":
                    new_time = new_time.shift(months=12)
                    if row.Date.end:
                        new_end = new_end.shift(months=12)
                elif row.Repeats == "Biannually":
                    new_time = new_time.shift(months=24)
                    if row.Date.end:
                        new_end = new_end.shift(months=24)
                elif row.Repeats == "Custom":
                    if row.CustomRepeatDuration:
                        if row.CustomRepeatDuration > 0:
                            t = (arrow.now() - new_time).days / row.CustomRepeatDuration
                            new_time = new_time.shift(
                                days=ceil(t) * row.CustomRepeatDuration if t >= 1 else row.CustomRepeatDuration)
                        else:
                            # row.set_property("Repeats", "Please enter a custom repeat duration > 0")
                            fail = True
                            break
                    else:
                        # row.set_property("Repeats", "Please enter a custom repeat duration > 0")
                        fail = True
                        break
                else:
                    # row.set_property("Repeats", "Error: Invalid Option Selected")
                    fail = True
                    break

            if not fail:
                if ":" in row.Date.start.__str__():
                    if row.Date.end:
                        notion_date = NotionDate(start=new_time.datetime, timezone=row.Date.timezone,
                                                 end=new_end.datetime, reminder=row.Date.reminder)

                    else:
                        notion_date = NotionDate(start=new_time.datetime, timezone=row.Date.timezone, reminder=row.Date.reminder)
                    row.set_property("Date", notion_date)
                    print("Datetime " + new_time.datetime.__str__())
                else:
                    if row.Date.end:
                        notion_date = NotionDate(start=new_time.date(),
                                                 end=new_end.date(), reminder=row.Date.reminder)
                    else:
                        notion_date = NotionDate(start=new_time.date(), reminder=row.Date.reminder)

                    row.set_property("Date", notion_date)
                    print("Date " + new_time.date().__str__())


main()
