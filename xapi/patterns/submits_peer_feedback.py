import re
from django.conf import settings
from tincan import (
    Activity,
    ActivityDefinition,
    LanguageMap
)
from xapi.patterns.base import BasePattern
from xapi.patterns.eco_verbs import LearnerSubmitsPeerFeedbackVerb


class SubmitsPeerFeedbackRule(BasePattern, LearnerSubmitsPeerFeedbackVerb):
    def match(self, evt, course_id):
        reg = '/courses/'+settings.COURSE_ID_PATTERN
        reg += r'/xblock/[\S]+/handler/peer_assess/?'
        return re.match(reg, evt['event_type'])

    def convert(self, evt, course_id):
        verb = self.get_verb()
        obj = Activity(
            id=self.get_object_id(evt['context']['path']),
            definition=ActivityDefinition(
                name=LanguageMap({'en-US': evt['event_type'].split('peer_assess')[0]}),
                type="http://www.ecolearning.eu/expapi/activitytype/peerassessment"
            )
        )
        return verb, obj
