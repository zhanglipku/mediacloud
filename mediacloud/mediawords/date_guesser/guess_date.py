import arrow
from bs4 import BeautifulSoup

from .constants import Accuracy, LOCALE, GuessMethod, Guess
from .dates import MultiDateParser
from .html import get_tag_checkers, get_image_url_checker
from .urls import parse_url_for_date


class DateGuesser(object):
    def __init__(self):
        self.parser = MultiDateParser(arrow.parser.DateTimeParser(locale=LOCALE))
        self.tag_checkers = get_tag_checkers()
        self.image_url_checker = get_image_url_checker()

    def _choose_better_guess(self, current, new):
        """Logic for deciding if a new guess is better than the previous.

        Attributes
        ----------
        current : (datetime or None, Accuracy)
            Current datetime and accuracy
        new : (datetime or None, Accuracy)
            Proposed datetime and accuracy

        Returns
        -------
        (datetime or None, Accuracy)
            Either current or new
        """
        if current.accuracy >= new.accuracy:
            return current
        elif current.accuracy is Accuracy.NONE:
            return new
        elif current.accuracy is Accuracy.PARTIAL:  # year and month should be right-ish
            if abs((current.date.date() - new.date.date()).days) < 45:
                return new
        elif current.accuracy is Accuracy.DATE:
            if abs((current.date.date() - new.date.date()).days) < 2:
                return new
        return current

    def guess_date(self, url, html):
        """Guess the date of publication of a webpage.

        Attributes
        ----------
        url : str
            url used to retrieve the webpage
        html : str
            raw html of the webpage

        Returns
        -------
        (datetime or None, Accuracy)
            In case a reasonable guess can be made, returns a datetime and Enum of accuracy
        """
        # default guess
        guess = Guess(None, Accuracy.NONE, GuessMethod.NONE)
        # Try using the url
        guess = self._choose_better_guess(guess, parse_url_for_date(url))

        # Try looking for specific elements
        soup = BeautifulSoup(html, 'lxml')
        for tag_checker in self.tag_checkers:
            date_string = tag_checker(soup)
            new_date, new_accuracy = self.parser.parse(date_string)
            new_guess = Guess(new_date, new_accuracy, GuessMethod.HTML)
            guess = self._choose_better_guess(guess, new_guess)

        # Try og:image tag to extract a url with a date string
        image_url = self.image_url_checker(soup)
        if image_url is not None:
            guess = self._choose_better_guess(guess, parse_url_for_date(image_url))

        return guess
