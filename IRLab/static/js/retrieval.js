const POLL_INTERVAL = 30000; // 30 seconds
const POLL_URL = "/poll/evaluation/update"
/**
 * Polls the django server checking for changes in ranking function evaluations.
 * If a change is detected, the page is reloaded to apply the changes.
 */
const pollForEvaluationResults = function() {
    $.post(POLL_URL, data=JSON.stringify({rankers: evalRankers}), function(response) {
        if (response == "200") {
            location.reload(true);
        }
    });
}

setInterval(pollForEvaluationResults, POLL_INTERVAL);