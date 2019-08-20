import React from 'react'
import { shallow,render,mount,configure } from 'enzyme'
import Adapter from 'enzyme-adapter-react-16';

import onBoardingPage from '../../components/pages/authPage.jsx'
import {LoginFormContainer} from '../../components/auth/loginForm.jsx'

configure({ adapter: new Adapter() });

describe('authPage Tests', () => {
    test('render onBoarding page', () => {
        const onBoardingPage = shallow(
            <onBoardingPage/>
        );
        expect(onBoardingPage.exists()).toBe(true);
    });

    test('render onBoarding page login', () => {
        const wrapper = shallow(
            <onBoardingPage login={true} />
        );
        expect(wrapper.find(<LoginFormContainer/>).exists()).toBe(true);
    });
});