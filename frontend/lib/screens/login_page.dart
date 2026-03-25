import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import 'home_page.dart';

class LoginPage extends StatefulWidget
{
  @override
  _LoginPageState createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage>
{
  TextEditingController user = TextEditingController();
  TextEditingController pass = TextEditingController();
  String err = "";

  void login()
  {
    if(AuthService.login(user.text, pass.text))
    {
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => HomePage()));
    }
    else
    {
      setState(() { err = "invalid login"; });
    }
  }

  @override
  Widget build(BuildContext context)
  {
    return Scaffold(
      body: Center(
        child: Padding(
          padding: EdgeInsets.all(20),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              TextField(controller: user, decoration: InputDecoration(labelText: "username")),
              TextField(controller: pass, obscureText: true, decoration: InputDecoration(labelText: "password")),
              SizedBox(height: 20),
              ElevatedButton(onPressed: login, child: Text("login")),
              Text(err, style: TextStyle(color: Colors.red))
            ],
          ),
        ),
      ),
    );
  }
}
