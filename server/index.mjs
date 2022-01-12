import express from 'express'
import {spawn} from 'child_process'
import dotenv from 'dotenv'

dotenv.config()

const app = express()
const port = process.env.PORT
const ip = process.env.IP

app.get('/', (req, res) => {
	
	try {
		let temperature = 'Error'
		const python = spawn('python3', ['./py/device.py'])
	
		python.stdout.on('data', function(data) {
			temperature = (data.toString());
			temperature = temperature.replace('\r\n', '')
			temperature = temperature.replace('\n', '')
		})

		python.on('close', (code)=>{
			console.log(`received: ${temperature} with code ${code} from sensor`)
			res.status(200).json({temperature: temperature})
		})
	}
	catch(err) {
		res.status(400).json({message: err.message})
	}
})


if (port === undefined || ip === undefined){
	console.log('Unable to retreive port or ip.')
} else {
	app.listen(port, ip, ()=>{
		console.log(`Server listening on ${ip}:${port}.`)
	})
}

