FROM --platform=linux/amd64 python:3.10.12
WORKDIR /opt/app
COPY code/* ./
RUN pip install -r requirements.txt
EXPOSE 8501
CMD streamlit run /opt/app/dashboard.py
# ENTRYPOINT streamlit run ./dashboard.py