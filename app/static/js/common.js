

async function processFormSubmission(form_id, message_id) {
  // Select all forms with the class "form-command"
  let forms = document.querySelectorAll(form_id);

  // Add an event listener to each form
  forms.forEach(form => {
    form.addEventListener('submit', async function(event) {
      event.preventDefault(); // Prevent the form from being submitted

      let error_message = $(message_id + '-error-message')
      let success_message = $(message_id + '-success-message')
      
      let formData = new FormData(event.target);
      let o_key = '';
      let object = {};

      for (let [key, value] of formData.entries()) {
        if (key !== 'update_type') {
          if (key === 'import-file') {
            // Parse the file and convert it to a JSON object
            value = await new Promise((resolve, reject) => {
              let reader = new FileReader();;
              reader.onload = function(e) {
                try {
                  let json = JSON.parse(e.target.result);
                  resolve(json);
                } catch (err) {
                  reject(err);
                }
              };
              reader.onerror = reject;
              reader.readAsText(value);
            });
            object[key] = value;
          } else {
            object[key] = value;
          }
        } else {
          o_key = value;
        }
      }

      object = {
        [o_key]: object
      }

      try {
        const response = await fetch("/api/update", {
          method: "POST",
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(object),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        } else {
          const data = await response.json();
          if (Object.keys(data)[0] === 'success') {
            error_message.hide();
            success_message.text(data['success']).fadeIn();
            setTimeout(function() {
              location.reload(); // This will refresh the page
            }, 1500);
          } else {
            error_message.text(data['error']).fadeIn();
          }
        }
      } catch (error) {
        console.error('An error occurred:', error);
      }
      event.preventDefault();
    });
  });
}

async function processForms(actions, id) {
  actions.forEach(action => {
      processFormSubmission(`#${action}-${id}-form`, `#${action}`);
    });
}

async function fadeOutAlert() {
  window.setTimeout(function() {
      var alert = document.getElementById('alert-message');
      if (alert) {
          alert.className += ' fade-out';
          alert.addEventListener('animationend', function() {
              alert.style.display = 'none';
          });
      }
  }, 1000);
}

