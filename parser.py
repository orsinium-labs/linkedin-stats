from __future__ import annotations

import datetime
import json
import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import dateutil.parser
from emoji import EMOJI_DATA


COMPANIES = {
    '@fb.com',  # Meta
    'Amazon',
    'Ariga',
    'Biller',
    'Bitpanda',
    'BOTS',
    'Capgemini Client',
    'Capri Partners',
    'Crowdstrike',
    'DCVTechnologies',
    'Elastic',
    'Enreach',
    'Flexport',
    'FLYR Labs',
    'Form3',
    'GeekSoft Consulting',
    'HCL Technologies',
    'HelloFresh',
    'InDebted',
    'IndyKite',
    'Lightspeed',
    'M2A Media',
    'Makersite',
    'Marko',
    'Mollie',
    'Nebius',
    'NetData',
    'Orbis',
    'planet.com',  # Planet
    'Pollen',
    'PostNL',
    'Prodapt',
    'Seamly',
    'Sendcloud',
    'Sentinels',
    'Smart.pr',
    'Smiler',
    'TCS',  # Tata Consultancy Services
    'Tessian',
    'v7labs',
    'viafintech',
    'vpTech',
}


@dataclass
class Message:
    raw: str

    @cached_property
    def has_name(self) -> bool:
        if 'Gram' in self.raw:
            return True
        return 'Nikita' in self.raw

    @cached_property
    def read_cv(self) -> bool:
        return 'Gram' in self.raw

    @cached_property
    def autogenerated(self) -> bool:
        if 'Gram' in self.raw:
            return False
        # If there is no my name, assume autogenerated
        if 'Nikita' not in self.raw:
            return True
        return 'OR 1 --' in self.raw

    @cached_property
    def _name_time(self) -> tuple[str, str]:
        rex = re.compile(r'(.+)  ?(\d{1,2}:\d{1,2} [AP]M)')
        for line in self.raw.splitlines():
            match = rex.fullmatch(line)
            if match is None:
                continue
            name = match.group(1)
            time = match.group(2)
            return name, time
        raise LookupError

    @cached_property
    def sender_name(self) -> str:
        name = self._name_time[0]
        name = name.split('(')[0]  # remove pronouns
        name = name.strip()
        name = name.removesuffix(' sent the following messages at')
        assert name
        assert name[0] == name[0].capitalize()
        return name

    @cached_property
    def sender_pronouns(self) -> str:
        if 'she/' in self.raw.lower():
            return 'she'
        if 'he/' in self.raw.lower():
            return 'he'
        if 'they/' in self.raw.lower():
            return 'they'
        return ''

    @cached_property
    def time(self) -> datetime.time:
        time = self._name_time[1]
        return dateutil.parser.parse(time).time()

    @cached_property
    def sender_title(self) -> str:
        found_dot = False
        for line in self.raw.splitlines():
            if found_dot:
                return line
            if '· ' in line:
                found_dot = True
        return ''

    @cached_property
    def salary(self) -> tuple[str, str]:
        rex = re.compile(r'[€£]?(\d{2,3})(k|K|\,000)')
        matches = []
        for match in rex.finditer(self.raw):
            matches.append(match.group(1))
        if not matches:
            return ('', '')
        if len(set(matches)) == 1:
            return ('', matches[0])
        return tuple(matches[:2])  # type: ignore

    @cached_property
    def has_emoji(self) -> bool:
        for c in self.raw:
            if c in EMOJI_DATA:
                return True
        return False

    @cached_property
    def has_email(self) -> bool:
        rex = re.compile(r'.+@.+\.[a-z]{2,3}')
        return rex.search(self.raw) is not None

    @cached_property
    def has_url(self) -> bool:
        return 'https://' in self.raw or 'www.' in self.raw

    @cached_property
    def company(self) -> str:
        for company in COMPANIES:
            if company in self.raw:
                return company
        return ''

    @cached_property
    def python(self) -> bool:
        return 'python' in self.raw.lower()

    @cached_property
    def date(self) -> datetime.date:
        rex = re.compile(r'\n[A-Z]{1}[A-Za-z]{2} \d{1,2}(, \d{4})?')
        match = rex.search(self.raw)
        assert match, self.sender_name
        return dateutil.parser.parse(match.group(0)).date()

    def as_dict(self) -> dict:
        return dict(
            # about the sender
            sender_name=self.sender_name,
            sender_title=self.sender_title,
            sender_pronouns=self.sender_pronouns,

            # about the message
            has_name=self.has_name,
            read_cv=self.read_cv,
            autogenerated=self.autogenerated,
            salary_low=self.salary[0],
            salary_high=self.salary[1],
            has_emoji=self.has_emoji,
            has_email=self.has_email,
            has_url=self.has_url,
            company=self.company,
            python=self.python,
            chars=len(self.raw),
            date=self.date.strftime('%Y-%m-%d'),
            time=self.time.strftime('%H:%I'),
        )


def main() -> None:
    raws = Path('raw.txt').read_text().split('\n\n\n\n\n')
    raws = [raw.strip() for raw in raws]
    raws = [raw for raw in raws if raw]
    for raw in raws:
        parsed = Message(raw).as_dict()
        print(json.dumps(parsed))


if __name__ == '__main__':
    main()
