import dataclasses
import itertools
import unittest

from cgc.experimental.quiescence import Claim, Profile, Truth, OBLIGATIONS, assess
from cgc.experimental.orchestration import Action, plan_attempt, execute


def profile(statuses=None, **changes):
    values = dict(project='fixture', generation='g1', observed_ns=10, expires_ns=20,
                  claims=tuple(Claim(k, s) for k, s in zip(OBLIGATIONS, statuses or [Truth.YES]*6)))
    values.update(changes)
    return Profile(**values)


class ChildQuiescenceTests(unittest.TestCase):
    def test_all_compositions_never_promote_production(self):
        for statuses in itertools.product(Truth, repeat=6):
            with self.subTest(statuses=statuses):
                out=assess(profile(statuses),project='fixture',generation='g1',now_ns=11)
                expected=Truth.NO if Truth.NO in statuses else Truth.UNKNOWN if Truth.UNKNOWN in statuses else Truth.YES
                self.assertIs(out.model_result,expected)
                self.assertIs(out.production_p3,Truth.UNKNOWN)
                self.assertFalse(out.mutation_authorized)

    def test_each_missing_obligation(self):
        for i in range(6):
            statuses=[Truth.YES]*6;statuses[i]=Truth.UNKNOWN
            self.assertIs(assess(profile(statuses),project='fixture',generation='g1',now_ns=11).model_result,Truth.UNKNOWN)

    def test_clock_and_scope_and_import(self):
        for now,project,generation in ((9,'fixture','g1'),(20,'fixture','g1'),(11,'other','g1'),(11,'fixture','g2')):
            self.assertIs(assess(profile(),project=project,generation=generation,now_ns=now).model_result,Truth.UNKNOWN)
        self.assertIs(assess(profile(provenance='IMPORTED'),project='fixture',generation='g1',now_ns=11).model_result,Truth.UNKNOWN)

    def test_invalid_schema(self):
        for changes in ({'claims':()}, {'claims':list(profile().claims)}, {'observed_ns':True},
                        {'expires_ns':9}, {'expires_ns':10**12}, {'project':'../x'},
                        {'provenance':'LIVE'}, {'generation':'é'}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):profile(**changes)
        with self.assertRaises(ValueError):Claim('domain_empty','YES')
        with self.assertRaises(ValueError):profile(claims=tuple(reversed(profile().claims)))

    def test_immutable(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):profile().generation='forged'

    def test_attempts_and_recovery_refuse(self):
        for action,prior in itertools.product(Action,('NONE','SUCCEEDED','FAILED','UNCERTAIN')):
            p=plan_attempt(action,profile(),project='fixture',generation='g1',now_ns=11,previous_attempt=prior)
            self.assertFalse(p.mutation_authorized)
            self.assertEqual(p.state,'BLOCKED')
            if prior=='UNCERTAIN':self.assertIn('UNCERTAIN_PREVIOUS_ATTEMPT_REQUIRES_REVIEW',p.blockers)
            with self.assertRaisesRegex(RuntimeError,'NO_ACCEPTED_EXECUTION_ADAPTER'):execute(p)
        with self.assertRaises(RuntimeError):execute({'mutation_authorized':True,'production_p3':'YES'})


if __name__=='__main__':unittest.main()
