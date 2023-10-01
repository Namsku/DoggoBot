async function request(url, method = 'GET', data = null) {
    try {
        const requestOptions = {
            url: url, // API endpoint URL
            dataType: 'json', // Expect JSON response
            contentType: 'application/json', // Request content type for POST requests
        };

        if (method === 'POST') {
            requestOptions.method = 'POST';
            requestOptions.data = JSON.stringify(data); // Request data for POST requests
        }

        const response = await $.ajax(requestOptions);

        // Return the API response data
        return response;
    } catch (error) {
        // Handle errors here
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

async function user_stats_stack() {
    datasets = []
    i = 0
    _labels = JSON.parse(await request('/api/users_stats'));
    bg_color = ['#990011', '#FFA351', '#2BAE66', '#D9E5D6', '#FFC0CB']
    for (const key in _labels)   
        datasets.push({
            label: key,
            backgroundColor: bg_color[i],
            data: _labels[key] // Array of values
        })
        i += 1


    var data = {
        labels: Object.keys(_labels),
        datasets
    };

    var ctx = document.getElementById('myChart').getContext('2d');

    var myChart = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            indexAxis: 'y',
            responsive: false,
            scales: {
                x: {
                    stacked: true,
                },
                y: {
                    stacked: true
                }
            }
        }
    });

    myChart.canvas.parentNode.style.height = '250px';
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

async function addClickEventListenersToSwitchButtons(database_name, attribute_name) {
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