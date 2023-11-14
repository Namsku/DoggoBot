async function fetch_request(url, options) {
    const response = await fetch(url, options);
  
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  
    const json = await response.json();
  
    return json;
  }

async function request(url, method = 'GET', data = null) {
    try {
      const headers = {
        'Content-Type': 'application/json'
      };
  
      const options = {
        method: method,
        headers: headers,
        credentials: 'same-origin'
      };
  
      if (data) {
        options.body = JSON.stringify(data);
      }
  
      const response = await fetch_request(url, options);
  
      return response;
    } catch (error) {
      console.error('Error:', error);
      throw error;
    }
}

async function top_chatters_stats() {
    var ctx = document.getElementById('chatters-histogram').getContext('2d');
    _labels = JSON.parse(await request('/api/chatters_stats'));
    var chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(_labels),
            datasets: [{
                label: 'Users',
                data: Object.values(_labels),
                backgroundColor: ['#990011', '#FFA351', '#2BAE66', '#D9E5D6', '#FFC0CB'],
            }]
        },
        options: {
            title: {
                display: true,
                text: 'Top 5 Chatters'
            },
            indexAxis: 'y',
            maintainAspectRatio: false,
            plugins: {
                datalabels: {
                    formatter: function(value, context) {
                        return value + '%';
                    }
                }
            }
        }
    });

    chart.canvas.parentNode.style.height = '250px';
    chart.canvas.parentNode.style.margin = '0 auto';
}

async function user_stats_pie() {
    var ctx = document.getElementById('user-chart').getContext('2d');
    _labels = JSON.parse(await request('/api/users_stats'));
    var chart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(_labels),
            datasets: [{
                label: 'Pie Chart',
                data: Object.values(_labels),
                backgroundColor: ['#990011', '#FFA351', '#2BAE66', '#D9E5D6'],
            }]
        },
        options: {
            title: {
                display: true,
                text: 'User Stats'
            },
            labelsPosition: 'outside',
            plugins: {
                datalabels: {
                    formatter: function(value, context) {
                        return value + '%';
                    }
                }
                
            }
        }
    });

    chart.canvas.parentNode.style.width = '250px';
    chart.canvas.parentNode.style.height = '250px';
    chart.canvas.parentNode.style.margin = '0 auto';
}

async function send_message(object) {
    const response = await request('/api/update', 'POST', object);
    console.log(response);
}

async function event_listener_switch_butons(database_name, attribute_name) {
    // Get all switch button elements with IDs starting with "switch-"
    const switchButtons = document.querySelectorAll('[id^="switch-"]');

    // Add a click event listener to each switch button
    switchButtons.forEach(switchButton => {
        switchButton.addEventListener('click', function() {
        // Get the value of the switch button
        
        object = {
             [database_name] : {
                'attribute': attribute_name,
                'name': switchButton.id.split('-')[1],
                'status': switchButton.checked
            }            
        }

        request('/api/update', method='POST', data=object);
    });
  });
}


function setupModal(modalId, buttonId) {
  $(document).ready(function() {
    const popupForm = $(modalId);
    const modalContent = popupForm.find(".modal-content");

    // Open popup form when open button is clicked
    $(buttonId).click(function() {
      popupForm.modal("show");
    });

    // Add smooth animation to popup form
    popupForm.on("show.bs.modal", function() {
      modalContent.css({
        "transform": "scale(1)",
        "opacity": 0
      }).animate({
        "transform": "scale(1)",
        "opacity": 1
      }, 200);
    });

    // Add darker background to popup form
    popupForm.on("show.bs.modal", function() {
      $("body").addClass("modal-open");
      $(".modal-backdrop").addClass("bg-dark");
    });

    // Remove darker background from popup form when it is closed
    popupForm.on("hidden.bs.modal", function() {
      $("body").removeClass("modal-open");
      $(".modal-backdrop").removeClass("bg-dark");
    });
  });
}

async function form_delete_command() {
  setupModal("#deleteModal", "#open-delete-form-btn");
}

async function form_edit_command() {
  setupModal("#popup-edit-form", "#open-edit-form-btn");
}

async function form_create_command() {
  setupModal("#popup-form", "#open-form-btn");
}

async function handle_submit_form() {
  await document.querySelector('#form-command').addEventListener('submit', function(event) {
    event.preventDefault();
    
    var formData = new FormData(event.target);
    var o_key = '';
    let object = {};


    for (let [key, value] of formData.entries()) {
      if (key != 'update_type') {
        object[key] = value;
      } else {
        o_key = value;
      }
    }

    object = {
      [o_key]: object
    }

    let json = JSON.stringify(object);

    fetch("/api/update", {
      method: "POST",
      body: json,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log(data);
      })
      .catch((error) => {
        console.log(error)
        // Handle the error.
      });
  });
}

async function handle_event(form_id=None, name=None) {
    if (form_id) {
        await handle_submit_form(form_id, '/api/update');
    }

      // Send the form data to the API
      const response = await fetch('/api/update', {
        method: 'POST',
        body: formData
      });
  
      return response.json();
}

async function delete_command(name) {
      const response = await fetch('/api/update', {
        method: 'POST',
        body: formData
      });
  
      return response.json();
}

async function update_user_command_table() {
    const user_table = document.getElementById('user-commands');
    const response = await fetch('/api/commands');
    const json = await response.json();

    json.forEach((item) => {
      const row = document.createElement('tr');
      const nameCell = document.createElement('td');
      const emailCell = document.createElement('td');

      nameCell.textContent = item.name;
      emailCell.textContent = item.email;

      row.appendChild(nameCell);
      row.appendChild(emailCell);

      user_table.appendChild(row);
    });
}

function createModal(title, id) {
    // Create elements
    let modal = document.createElement('div');
    modal.id = 'popup-form';
    modal.className = 'modal fade';
    modal.tabIndex = '-1';
    modal.role = 'dialog';
    modal.setAttribute('aria-labelledby', 'popupFormLabel');
    modal.setAttribute('aria-hidden', 'true');

    let modalDialog = document.createElement('div');
    modalDialog.className = 'modal-dialog';

    let modalContent = document.createElement('div');
    modalContent.className = 'modal-content';

    let modalHeader = document.createElement('div');
    modalHeader.className = 'modal-header';

    let modalTitle = document.createElement('h5');
    modalTitle.className = 'modal-title';
    modalTitle.id = 'popupFormLabel';
    modalTitle.textContent = title

    let closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'btn-close';
    closeButton.setAttribute('data-bs-dismiss', 'modal');
    closeButton.setAttribute('aria-label', 'Close');

    let modalBody = document.createElement('div');
    modalBody.className = 'modal-body';

    let form = document.createElement('form');
    form.id = 'form-command';

    // ... continue creating all elements ...

    // Append elements
    modalHeader.appendChild(modalTitle);
    modalHeader.appendChild(closeButton);
    modalContent.appendChild(modalHeader);
    modalContent.appendChild(modalBody);
    modalDialog.appendChild(modalContent);
    modal.appendChild(modalDialog);

    // Append modal to body
    document.body.appendChild(modal);
}
