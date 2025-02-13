import axios from 'axios';

async function getGasPrice() {
  try {
    const response = await axios.get('https://api.polygonscan.com/api', {
      params: {
        module: 'gastracker',
        action: 'gasoracle',
        apikey: process.env.POLYGONSCAN_API_KEY,
      },
    });

    if (response.data.status === '1') {
      const { SafeGasPrice, ProposeGasPrice, FastGasPrice } = response.data.result;
      console.log('SafeGasPrice:', SafeGasPrice);
      console.log('ProposeGasPrice:', ProposeGasPrice);
      console.log('FastGasPrice:', FastGasPrice);
    } else {
      console.error('Error fetching gas prices:', response.data.message);
    }
  } catch (error: any) {
    console.error('Error:', error.message);
  }
}

getGasPrice().catch(error => console.error('Unhandled error:', error));
