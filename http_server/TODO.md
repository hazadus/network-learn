# HTTP Server ToDos

- [X] Handle various MIME types by file extension.
- [X] Add support for showing a directory listing. If the user doesn’t specify a file in the URL, show a directory 
  listing where each file name is a link to that file.
- [ ] Add more MIME types, test with m4a, mp4.
- [ ] Configure logging.
- [ ] Modify the client to be able to send payloads. You’ll need to be able to set the Content-Type and Content-Length based on the payload.
- [ ] Modify the server to extract and print a payload sent by the client.
- [ ] Загрузка файла по HTTP на сервер через форму
- [ ] Параметризованные декораторы для определения routes

## References 

- https://beej.us/guide/bgnet0/html/split/project-a-better-web-server.html
- https://beej.us/guide/bgnet0/html/split/project-http-client-and-server.html
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types