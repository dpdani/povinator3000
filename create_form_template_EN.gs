/*

This script was generated automagically by Povinator3000,
on {{ dt }}.

*/


function main() {
  var form = FormApp.create("{{ title }}");
  
  form.setCollectEmail(true);
  form.setRequireLogin(true);
  form.setLimitOneResponsePerUser(true);
  
  form.addImageItem()
      .setImage(DriveApp.getFileById("10mKV2-q0BlvfXxTZ0xrlbUjmDdZVS_1C"))
      .setAlignment(FormApp.Alignment.CENTER);
  
  form.addTextItem()
      .setTitle("First name")
      .setRequired(true);
  form.addTextItem()
      .setTitle("Last name")
      .setRequired(true);
  form.addDateItem()
      .setTitle("Date of Presentation")
      .setRequired(true);
  form.addMultipleChoiceItem()
      .setTitle("Degree Level")
      .setChoiceValues(["Bachelor", "Master"])
      .setRequired(true);
  form.addMultipleChoiceItem()
      .setTitle("Department / Faculty")
      .setChoiceValues([{% for dep in departments %}"{{ dep }}", {% endfor %}])  // ["CIBIO", "DISI"]
      .setRequired(true);
  
  {% for dep in departments %}
  form.addPageBreakItem()
      .setTitle("CIBIO")
      .setHelpText("Please, double check you are specifying the correct Commission.");
  form.addMultipleChoiceItem()
      .setTitle("Commission")
      .setChoiceValues([{% for com in commissions[dep] %}"{{ com }}", {% endfor %} "I don't know"])
      .setRequired(true);
  {% endfor %}
    
  form.addPageBreakItem()
      .setTitle("Your Presentation")
      .setHelpText("Only upload presentation or PDF files.");
  
  form.setConfirmationMessage("In bocca al lupo!\n\nRemember that you can edit your submission using the confirmation mail that you should receive in a few moments.");
  
  form.setAcceptingResponses(true);
  form.setAllowResponseEdits(true);
}

