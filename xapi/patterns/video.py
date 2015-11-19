from tincan import (
    Activity,
    ActivityDefinition,
    LanguageMap
)
from xapi.patterns.base import BasePattern
from xapi.patterns.eco_verbs import (
    LoadVideoVerb,
    PlayVideoVerb
)


class BaseVideoRule(BasePattern):  # pylint: disable=abstract-method

    def convert(self, evt, course_id):
        verb = self.get_verb()  # pylint: disable=no-member
        obj = Activity(
            id=self.fix_id(self.base_url, evt['page']),
            definition=ActivityDefinition(
                name=LanguageMap({'en-US': evt['event']['id']}),
                type="http://activitystrea.ms/schema/1.0/video"
            )
        )
        return verb, obj


class PlayVideoRule(BaseVideoRule, PlayVideoVerb):
    def match(self, evt, course_id):
        return (evt['event_type'] == 'play_video' and
                evt['event_source'] == 'browser')


class LoadVideoRule(BaseVideoRule, LoadVideoVerb):
    def match(self, evt, course_id):
        return (evt['event_type'] == 'load_video' and
                evt['event_source'] == 'browser')