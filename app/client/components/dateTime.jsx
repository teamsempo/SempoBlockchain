import React from 'react'
import moment from 'moment'


export default class DateTime extends React.Component {
    render() {
        console.log(this.props)
        if (this.props.created) {

            var formatted_time = moment.utc(this.props.created).fromNow();

            return (
                <div style={{margin: 0}}>{formatted_time}</div>
            )
        } else {
            return (
                <div style={{margin: 0}}>Not long ago</div>
            )
        }
    };
};