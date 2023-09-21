async function makeApiRequest(url) {
    try {
        const response = await $.ajax({
            url: url, // API endpoint URL
            method: 'GET',
            dataType: 'json', // Expect JSON response
        });

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
    _labels = JSON.parse(await makeApiRequest('/api/chatters_stats'));
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
    _labels = JSON.parse(await makeApiRequest('/api/users_stats'));
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
    _labels = JSON.parse(await makeApiRequest('/api/users_stats'));
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