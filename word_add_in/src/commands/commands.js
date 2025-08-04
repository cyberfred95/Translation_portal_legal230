/* global Office */

Office.onReady(() => {
  // Initialize commands
});

function showTaskpane(event) {
  // Show taskpane
  event.completed();
}

// Register functions
Office.actions.associate("showTaskpane", showTaskpane);
