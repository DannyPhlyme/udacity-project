/*
 * ensure all variables on this page match your project
 */

export const environment = {
  production: true,
  apiServerUrl: 'https://127.0.0.1:5000', // the running FLASK api server url
  auth0: {
    url: 'startercode.auth0.com', // the auth0 domain prefix
    audience: 'coffee', // the audience set for the auth0 app
    clientId: 'GX7r3zHg8ITgtWQR65pj5cFp6k631I1s', // the client id generated for the auth0 app
    callbackURL: 'http://localhost:8100', // the base url of the running ionic application. 
  }
};
