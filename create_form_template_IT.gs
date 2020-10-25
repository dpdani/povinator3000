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
      .setTitle("Nome")
      .setRequired(true);
  form.addTextItem()
      .setTitle("Cognome")
      .setRequired(true);
  form.addDateItem()
      .setTitle("Data della Presentazione")
      .setRequired(true);
  form.addMultipleChoiceItem()
      .setTitle("Livello di Laurea")
      .setChoiceValues(["Triennale", "Magistrale"])
      .setRequired(true);
  form.addMultipleChoiceItem()
      .setTitle("Dipartimento / Facoltà")
      .setChoiceValues([{% for dep in departments %}"{{ dep }}", {% endfor %}])  // ["CIBIO", "DISI"]
      .setRequired(true);
  
  {% for dep in departments %}
  form.addPageBreakItem()
      .setTitle("{{ dep }}")
      .setHelpText("Per favore, assicurati di specificare la Commissione corretta.");
  form.addMultipleChoiceItem()
      .setTitle("Commissione")
      .setChoiceValues([{% for com in commissions[dep] %}"{{ com }}", {% endfor %} "Non so"])
      .setRequired(true);
  {% endfor %}
  
  form.addPageBreakItem()
      .setTitle("La tua Presentazione")
      .setHelpText("Carica solamente file di presentazione o PDF.");
  
  form.setConfirmationMessage("In bocca al lupo!\n\nRicorda che puoi modificare le tue risposte utilizzando la mail di conferma che dovrebbe arrivarti a momenti.");
  
  form.setAcceptingResponses(true);
  form.setAllowResponseEdits(true);
}
