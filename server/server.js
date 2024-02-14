const axios = require('axios');
const cron = require('node-cron');

// Replace the URL with the actual API endpoint
const apiUrl = 'https://py-telegramjoshua.mobiloitte.io/push_chatid';

function makeApiCall() {
  axios.get(apiUrl)
    .then(response => {
      console.log('API Response:', response.data);
      // Handle the API response here
    })
    .catch(error => {
      console.error('Error making API call:', error.message);
      // Handle the error here
    });
}

// Schedule the API call every 10 seconds using cron syntax
cron.schedule('*/10 * * * *', makeApiCall);