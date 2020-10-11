# To run all tests, use `run_tests.sh discover`
# To run a particular test file, use `run_tests.sh test.event.test_lead_action_event`
# To run a particular test suite, use `run_tests.sh test.game.DrawTestCase`
# To run a particular test case, use `run_tests.sh test.game.DrawTestCase.test_removes_card_from_deck`

set -eu

PYTHONPATH='.:./test' python -m unittest "$@"
