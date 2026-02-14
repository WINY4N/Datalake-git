from flask import Flask, render_template, request, send_file
import requests
import json
import io

app = Flask(__name__)

ACCOUNT_NAME = "testkkuwebappputdata"
CONTAINER_NAME = "rawdata"
SAS_TOKEN = "?sv=2024-11-04&ss=bfqt&srt=sco&sp=rwdlacupx&se=2026-02-13T02:16:19Z&st=2026-02-11T18:01:19Z&spr=https&sig=SrUSoyfZJxmezoEcp5bi8ra70%2BXJzSXV0dL6LJYES98%3D" 

def get_url(file_name):
    token = SAS_TOKEN.strip()
    if not token.startswith("?"): token = "?" + token
    return f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/{file_name}{token}"

def read_file_content(response):
    try:
        text = response.content.decode('utf-8')
        try:
            json_obj = json.loads(text)
            return json.dumps(json_obj, indent=2, ensure_ascii=False)
        except:
            return text
    except UnicodeDecodeError:
        return f"[System] Binary content detected. Size: {len(response.content)} bytes. Please use Download."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/push', methods=['POST'])
def push_data():
    filename = request.form.get('filename')
    content = request.form.get('content')
    
    data = {"content": content, "source": "DevOps_Console"}
    json_data = json.dumps(data)
    headers = {"x-ms-blob-type": "BlockBlob", "Content-Type": "application/json"}
    
    try:
        url = get_url(filename)
        resp = requests.put(url, data=json_data.encode('utf-8'), headers=headers)
        if resp.status_code == 201:
            return render_template('index.html', msg=f"Success: File '{filename}' created.", status="success")
        else:
            return render_template('index.html', msg=f"Failed: {resp.text}", status="error")
    except Exception as e:
        return render_template('index.html', msg=f"Exception: {str(e)}", status="error")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return render_template('index.html', msg="Error: No file part in request.", status="error")
    file = request.files['file']
    if file.filename == '': return render_template('index.html', msg="Error: No file selected.", status="error")

    try:
        file_content = file.read()
        filename = file.filename
        content_type = file.content_type
        url = get_url(filename)
        headers = {"x-ms-blob-type": "BlockBlob", "Content-Type": content_type}
        
        resp = requests.put(url, data=file_content, headers=headers)
        if resp.status_code == 201:
            return render_template('index.html', msg=f"Success: File '{filename}' uploaded successfully.", status="success")
        else:
            return render_template('index.html', msg=f"Upload Failed: {resp.text}", status="error")
    except Exception as e:
        return render_template('index.html', msg=f"Exception: {str(e)}", status="error")

@app.route('/pull', methods=['POST'])
def pull_data():
    filename = request.form.get('filename')
    try:
        url = get_url(filename)
        resp = requests.get(url)
        
        if resp.status_code == 200:
            readable_text = read_file_content(resp)
            return render_template('index.html', msg=readable_text, status="info", is_text=True)
        elif resp.status_code == 404:
            return render_template('index.html', msg=f"Error 404: File '{filename}' not found.", status="error")
        else:
            return render_template('index.html', msg=f"Error: Status Code {resp.status_code}", status="error")
    except Exception as e:
        return render_template('index.html', msg=f"Exception: {str(e)}", status="error")

@app.route('/download', methods=['POST'])
def download_file():
    filename = request.form.get('filename')
    try:
        url = get_url(filename)
        resp = requests.get(url)
        
        if resp.status_code == 200:
            return send_file(
                io.BytesIO(resp.content),
                as_attachment=True,
                download_name=filename,
                mimetype=resp.headers.get('Content-Type')
            )
        elif resp.status_code == 404:
            return render_template('index.html', msg=f"Error 404: File '{filename}' not found.", status="error")
        else:
            return render_template('index.html', msg=f"Error: Status Code {resp.status_code}", status="error")
    except Exception as e:
        return render_template('index.html', msg=f"Exception: {str(e)}", status="error")

@app.route('/delete', methods=['POST'])
def delete_data():
    filename = request.form.get('filename')
    try:
        url = get_url(filename)
        resp = requests.delete(url)
        if resp.status_code == 202:
            return render_template('index.html', msg=f"Success: File '{filename}' deleted permanently.", status="success")
        elif resp.status_code == 404:
            return render_template('index.html', msg=f"Error 404: File '{filename}' does not exist.", status="error")
        else:
            return render_template('index.html', msg=f"Delete Failed: {resp.status_code}", status="error")
    except Exception as e:
        return render_template('index.html', msg=f"Exception: {str(e)}", status="error")

if __name__ == '__main__':
    app.run(debug=True, port=5000)