async function addSwitchButtonEventListeners(database_name, attribute_name) {
  const switchButtons = document.querySelectorAll('[id^="switch-"]');
  switchButtons.forEach(switchButton => {
      switchButton.addEventListener('click', function() {
          const object = {
              [database_name]: {
                  'attribute': attribute_name,
                  'name': switchButton.id.split('-')[1],
                  'status': switchButton.checked
              }
          }
          sendJsonRequest('/api/update', 'POST', object);
      });
  });
}

async function addEditButtonEventListeners() {
  const buttons = document.querySelectorAll('[id^="open-edit-form-btn-"]');

  buttons.forEach(button => {
      button.addEventListener('click', handleEditButtonClick);
  });

  async function handleEditButtonClick(event) {
      event.preventDefault();
      try {
          const response = await fetch("/api/command", {
              method: "POST",
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                  "command": event.target.id.split('-').pop()
              }),
          });

          if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
          }

          const data = await response.json();

          const popupEditForm = document.getElementById('popup-edit-form');
          const name = popupEditForm.querySelector('#name');
          const category = popupEditForm.querySelector('#category');
          const cost = popupEditForm.querySelector('#cost');
          const description = popupEditForm.querySelector('#description');

          name.value = data['name'];
          category.value = data['category'];
          cost.value = data['cost'];
          description.value = data['description'];
      } catch (error) {
          console.error('An error occurred:', error);
      }
  }
}


async function addEventListenerExportButton(id) {
  document.getElementById('export-btn').addEventListener('click', function() {
      generate_events_as_json(id);
  });
}

async function generate_events_as_json(id) {
  try {
      const response = await fetch(`/api/rpg/events/${id}`);
      const data = await response.json();
      const jsonData = JSON.parse(data);
      const blob = new Blob([JSON.stringify(jsonData, null, 4)], {
          type: 'application/json'
      });
      const url = URL.createObjectURL(blob);
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `rpg_events_{{ message['rpg'].name}}-${timestamp}.json`;

      createDownloadLink(url, filename);
  } catch (error) {
      console.error(error);
  }
}


function createDownloadLink(url, filename) {
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
}

function initializeModalAndButtonInteraction(modalId, buttonId) {
  $(document).ready(function() {
      const popupForm = $(modalId);
      const modalContent = popupForm.find(".modal-content");

      $(buttonId).click(function() {
          popupForm.modal("show");
      });

      popupForm.on("show.bs.modal", function() {
          modalContent.css({
              "transform": "scale(1)",
              "opacity": 0
          }).animate({
              "transform": "scale(1)",
              "opacity": 1
          }, 200);

          $("body").addClass("modal-open");
          $(".modal-backdrop").addClass("bg-dark");
      });

      popupForm.on("hidden.bs.modal", function() {
          $("body").removeClass("modal-open");
          $(".modal-backdrop").removeClass("bg-dark");
      });
  });
}

async function addEventListenerModalForms(action) {
  const buttons = document.querySelectorAll(`[id^="open-${action}-form-btn-"]`);
  buttons.forEach(button => {
      button.addEventListener('click', function() {
          if (action === 'delete') {
              document.getElementById('delete-name').value = button.id.split('-').pop();
          }
          initializeModalAndButtonInteraction(`#popup-${action}-form`, `#${button.id}`);
      });
  });
}

async function addFormEventListeners() {
  for (let action of ['create', 'edit', 'delete']) {
      addEventListenerModalForms(action);
  }
}