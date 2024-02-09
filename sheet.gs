function formatSheet() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var range = sheet.getRange('A2:G');
  
  // Set font to Lato, size 12, and make it bold for all cells
  range.setFontFamily('Lato');
  range.setFontSize(12);
  range.setFontWeight('bold');
  range.setHorizontalAlignment('left'); // Aligns content to the left
  
  // Set date and time columns (A and B) to dark purple
  var dateAndTimeRange = sheet.getRange('A2:B2');
  dateAndTimeRange.setFontColor('#5E2D79');
}

// automatically formats new data when it's added
function createOnEditTrigger() {
  var ss = SpreadsheetApp.getActive();
  ScriptApp.newTrigger('formatSheet')
      .forSpreadsheet(ss)
      .onEdit()
      .create();
}