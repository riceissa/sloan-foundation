#!/usr/bin/env python3

import bs4
from bs4 import BeautifulSoup


def main():
    first = True
    print("""insert into donations (donor, donee, amount, donation_date,
    donation_date_precision, donation_date_basis, cause_area, url,
    donor_cause_area_url, notes, affected_countries, affected_states,
    affected_cities, affected_regions) values""")

    with open("data.html", "r") as f:
        soup = BeautifulSoup(f, "lxml")
        data_list = soup.find("ul", {"class": "data-list"})
        for li in data_list:
            # Sometimes we get empty items so skip those
            if isinstance(li, bs4.element.NavigableString) and not li.strip():
                continue

            grantee = li.find("div", {"class": "grantee"}).text.strip()
            assert grantee.startswith("grantee:")
            grantee = grantee[len("grantee:"):].strip()

            amount = li.find("div", {"class": "amount"}).text.strip()
            assert amount.startswith("amount:")
            amount = amount[len("amount:"):].strip()
            assert amount.startswith("$")
            amount = float(amount.replace("$", "").replace(",", ""))

            # FIXME: I think this is the grantee's city, which is
            # different from affected_cities. Not sure if we want to
            # use it.
            city = li.find("div", {"class": "city"}).text.strip()
            assert city.startswith("city:")
            city = city[len("city:"):].strip()

            year = li.find("div", {"class": "year"}).text.strip()
            assert year.startswith("year:")
            year = year[len("year:"):].strip()

            details = li.find("div", {"class": "details"})
            description = details.find("div",
                                       {"class": "brief-description"}).text.strip()

            program = ""
            initiative = ""
            sub_program = ""
            investigator = ""
            for label in details.find_all("span", {"class": "label"}):
                label_text = label.text.strip()
                if label_text == "Program":
                    program = label.next_sibling.strip()
                elif label_text == "Initiative":
                    initiative = label.next_sibling.strip()
                elif label_text == "Sub-program":
                    sub_program = label.next_sibling.strip()
                elif label_text == "Investigator":
                    investigator = label.next_sibling.strip()

            notes = ((" grant investigator: " + investigator + ";" if investigator else "") +
                     (" initiative: " + initiative + ";" if initiative else "") +
                     " " + description[0].lower() + description[1:])
            notes = notes.strip()
            notes = notes[0].upper() + notes[1:]

            url = ("https://sloan.org" +
                   details.find("footer").find("a",
                                               {"class": "permalink"}).get("href"))

            print(("    " if first else "    ,") + "(" + ",".join([
                mysql_quote("Sloan Foundation"),  # donor
                mysql_quote(grantee),  # donee
                str(amount),  # amount
                mysql_quote(year + "-01-01"),  # donation_date
                mysql_quote("year"),  # donation_date_precision
                mysql_quote("donation log"),  # donation_date_basis
                mysql_quote(program + "/" + sub_program),  # cause_area
                mysql_quote(url),  # url
                mysql_quote("FIXME"),  # donor_cause_area_url
                mysql_quote(notes),  # notes
                mysql_quote(""),  # affected_countries
                mysql_quote(""),  # affected_states
                mysql_quote(""),  # affected_cities
                mysql_quote(""),  # affected_regions
            ]) + ")")
            first = False
        print(";")


def mysql_quote(x):
    '''
    Quote the string x using MySQL quoting rules. If x is the empty string,
    return "NULL". Probably not safe against maliciously formed strings, but
    whatever; our input is fixed and from a basically trustable source..
    '''
    if not x:
        return "NULL"
    x = x.replace("\\", "\\\\")
    x = x.replace("'", "''")
    x = x.replace("\n", "\\n")
    return "'{}'".format(x)


if __name__ == "__main__":
    main()
