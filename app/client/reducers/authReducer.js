export const REAUTH_REQUEST = 'REAUTH_REQUEST';

export const LOGIN_REQUEST = 'LOGIN_REQUEST';
export const LOGIN_PARTIAL = 'LOGIN_PARTIAL';
export const LOGIN_SUCCESS = 'LOGIN_SUCCESS';
export const LOGIN_FAILURE = 'LOGIN_FAILURE';
export const LOGOUT = 'LOGOUT';

export const REGISTER_REQUEST = 'REGISTER_REQUEST';
export const REGISTER_SUCCESS = 'REGISTER_SUCCESS';
export const REGISTER_FAILURE = 'REGISTER_FAILURE';
export const REGISTER_INACTIVE = 'REGISTER_INACTIVE';

export const ACTIVATE_REQUEST = 'ACTIVATE_REQUEST';
export const ACTIVATE_SUCCESS = 'ACTIVATE_SUCCESS';
export const ACTIVATE_FAILURE = 'ACTIVATE_FAILURE';

export const REQUEST_RESET_REQUEST = 'REQUEST_RESET_REQUEST';
export const REQUEST_RESET_SUCCESS = 'REQUEST_RESET_SUCCESS';
export const REQUEST_RESET_FAILURE = 'REQUEST_RESET_FAILURE';

export const RESET_PASSWORD_REQUEST = 'RESET_PASSWORD_REQUEST';
export const RESET_PASSWORD_SUCCESS = 'RESET_PASSWORD_SUCCESS';
export const RESET_PASSWORD_FAILURE = 'RESET_PASSWORD_FAILURE';

export const USER_LIST_REQUEST = 'USER_LIST_REQUEST';
export const USER_LIST_SUCCESS = 'USER_LIST_SUCCESS';
export const USER_LIST_FAILURE = 'USER_LIST_FAILURE';

export const UPDATE_USER_REQUEST = 'UPDATE_USER_REQUEST';
export const UPDATE_USER_SUCCESS = 'UPDATE_USER_SUCCESS';
export const UPDATE_USER_FAILURE = 'UPDATE_USER_FAILURE';

export const INVITE_USER_REQUEST = 'INVITE_USER_REQUEST';
export const INVITE_USER_SUCCESS = 'INVITE_USER_SUCCESS';
export const INVITE_USER_FAILURE = 'INVITE_USER_FAILURE';

export const VALIDATE_TFA_REQUEST = 'VALIDATE_TFA_REQUEST';
export const VALIDATE_TFA_SUCCESS = 'VALIDATE_TFA_SUCCESS';
export const VALIDATE_TFA_FAILURE = 'VALIDATE_TFA_FAILURE';


const initialLoginState = {
  isLoggingIn: false,
  token: null,
  userId: null,
  email: null,
  vendorId: null,
  usdToSatoshiRate: null,
  error: null,
  tfaURL: null,
  tfaFailure: false
};

export const login = (state = initialLoginState, action) => {
  switch (action.type) {
    case REAUTH_REQUEST:
    case LOGIN_REQUEST:
      return {...state, isLoggingIn: true};
    case LOGIN_SUCCESS:
      return {...state,
        isLoggingIn: false,
        token: action.token,
        userId: action.userId,
        vendorId: action.vendorId,
        email: action.email,
        adminTier: action.adminTier,
        usdToSatoshiRate: action.usdToSatoshiRate,
        tfaURL: null,
        tfaFailure: false};
    case LOGIN_PARTIAL:
      return {
        ...state,
        isLoggingIn: false,
        token: null,
        userId: null,
        tfaURL: action.tfaURL,
        tfaFailure: action.tfaFailure,
        error: action.error || 'unknown error'};
    case LOGIN_FAILURE:
      return {...state, isLoggingIn: false, token: null, userId: null, error: action.error || 'unknown error'};
    case LOGOUT:
      return initialLoginState;
    default:
      return state;
  }
};

const initialRegisterState = {
  isRegistering: false,
  registerSuccess: false,
  error: null
};

export const register = (state = initialRegisterState, action) => {
  switch (action.type) {
    case REGISTER_REQUEST:
      return {...state, isRegistering: true};
    case REGISTER_SUCCESS:
      return {...state, isRegistering: false, registerSuccess: true};
    case REGISTER_FAILURE:
      return {...state, isRegistering: false, registerSuccess: false, error: action.error || 'unknown error'};
    case REGISTER_INACTIVE:
      return initialRegisterState;
    default:
      return state;
  }
};


const initialActivateState = {
  isRegistering: false,
  registerSuccess: false,
  error: null
};

export const activate = (state = initialActivateState, action) => {
  switch (action.type) {
    case ACTIVATE_REQUEST:
      return {...state, isActivating: true};
    case ACTIVATE_SUCCESS:
      return {...state, isActivating: false, activateSuccess: true};
    case ACTIVATE_FAILURE:
      return {...state, isActivating: false, activateSuccess: false, error: action.error || 'unknown error'};
    default:
      return state;
  }
};

const initialRequestResetEmailState = {
  isRequesting: false,
  success: false,
  error: null
};

export const requestResetEmailState = (state = initialRequestResetEmailState, action) => {
  switch (action.type) {
    case REQUEST_RESET_REQUEST:
      return {...state, isRequesting: true};
    case REQUEST_RESET_SUCCESS:
      return {...state, isRequesting: false, success: true};
    case REQUEST_RESET_FAILURE:
      return {...state, isRequesting: false, success: false, error: action.error || 'unknown error'};
    default:
      return state;
  }
};

const inititialResetPasswordState = {
  isReseting: false,
  success: false,
  error: null
};

export const resetPasswordState = (state = inititialResetPasswordState, action) => {
  switch (action.type) {
    case RESET_PASSWORD_REQUEST:
      return {...state, isReseting: true};
    case RESET_PASSWORD_SUCCESS:
      return {...state, isReseting: false, success: true};
    case RESET_PASSWORD_FAILURE:
      return {...state, isReseting: false, success: false, error: action.error || 'unknown error'};
    default:
      return state;
  }
};

const initialUserListState = {
  isRequesting: false,
  success: false,
  error: null
};

export const userList = (state = initialUserListState, action) => {
  switch (action.type) {
    case USER_LIST_REQUEST:
      return {...state, isRequesting: true};
    case USER_LIST_SUCCESS:
      return {...state, isRequesting: false, success: true, userList: action.load_result.admin_list,};
    case USER_LIST_FAILURE:
      return {...state, isRequesting: false, success: false, error: action.error || 'unknown error'};
    default:
      return state;
  }
};

export const initialUpdateUserState = {
    isRequesting: false,
    success: false,
    error: null,
};

export const updateUserRequest = (state = initialUpdateUserState, action) => {
    switch (action.type) {
        case UPDATE_USER_REQUEST:
            return {...state, isRequesting: true, error: null, success: false};
        case UPDATE_USER_SUCCESS:
            return {...state, isRequesting: false, success: true};
        case UPDATE_USER_FAILURE:
            return {...state, isRequesting: false, error: action.error || 'unknown error'};
        default:
            return state;
    }
};

export const initialInviteUserState = {
    isRequesting: false,
    success: false,
    error: null,
};

export const inviteUserRequest = (state = initialInviteUserState, action) => {
    switch (action.type) {
        case INVITE_USER_REQUEST:
            return {...state, isRequesting: true, error: null, success: false};
        case INVITE_USER_SUCCESS:
            return {...state, isRequesting: false, success: true};
        case INVITE_USER_FAILURE:
            return {...state, isRequesting: false, error: action.error || 'unknown error'};
        default:
            return state;
    }
};

export const initialValidateTFAstate = {
    isRequesting: false,
    success: false,
    error: null,
};

export const validateTFA = (state = initialValidateTFAstate, action) => {
    switch (action.type) {
        case VALIDATE_TFA_REQUEST:
            return {...state, isRequesting: true, error: null, success: false};
        case VALIDATE_TFA_SUCCESS:
            return {...state, isRequesting: false, success: true};
        case VALIDATE_TFA_FAILURE:
            return {...state, isRequesting: false, error: action.error || 'unknown error'};
        default:
            return state;
    }
};

// ACTIONS
export const loginRequest = (payload) => (
  {
    type: LOGIN_REQUEST,
    payload,
  }
);

export const validateTFARequest = (payload) => (
  {
    type: VALIDATE_TFA_REQUEST,
    payload
  }
);

export const loginSuccess = (idToken) => (
  {
    type: LOGIN_SUCCESS,
    idToken
  }
);

export const loginFailure = error => (
  {
    type: LOGIN_FAILURE,
    error
  }
);

export const logout = () => (
  {
    type: LOGOUT
  }
);


export const registerRequest = (payload) => (
  {
    type: REGISTER_REQUEST,
    payload
  }
);

export const registerSuccess = () => (
  {
    type: LOGIN_SUCCESS
  }
);

export const registerFailure = error => (
  {
    type: REGISTER_FAILURE,
    error
  }
);

export const deactivateRegister = () => (
  {
    type: REGISTER_INACTIVE
  }
);

export const activateAccount = activation_token => (
  {
    type: ACTIVATE_REQUEST,
    activation_token
  }
);

export const requestPasswordResetEmail = email => (
  {
    type: REQUEST_RESET_REQUEST,
    email
  }
);

export const resetPassword = payload => (
  {
    type: RESET_PASSWORD_REQUEST,
    payload
  }
);

export const loadUserList = () => (
  {
    type: USER_LIST_REQUEST,
  }
);

export const updateUser = (payload) => (
  {
    type: UPDATE_USER_REQUEST,
    payload
  }
);

export const inviteUser = (payload) => (
  {
    type: INVITE_USER_REQUEST,
    payload
  }
);

